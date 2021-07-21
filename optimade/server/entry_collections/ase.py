from functools import lru_cache
from time import strftime, gmtime
from typing import Any, Callable, Dict, Generator, List, NamedTuple, Tuple

from ase.db import connect
from ase.db.core import T2000, YEAR
from ase.db.row import AtomsRow
from ase.formula import Formula, dict2str

from optimade.filterparser import LarkParser
from optimade.filtertransformers.ase import ASEQueryTree, ASETransformer
from optimade.models import EntryResource
from optimade.server.config import CONFIG
from optimade.server.entry_collections import EntryCollection

# from optimade.server.logger import LOGGER
from optimade.server.mappers import BaseResourceMapper

INF = 9999999999999


class ASECollection(EntryCollection):
    def __init__(
        self,
        name: str,
        resource_cls: EntryResource,
        resource_mapper: BaseResourceMapper,
        database: str = CONFIG.ase_database,
    ):

        super().__init__(resource_cls, resource_mapper, ASETransformer())

        self.parser = LarkParser(version=(1, 0, 0), variant="default")
        self.collection = ASEDBWrapper(database)

    def __len__(self) -> int:
        """Returns the total number of entries in the collection."""
        return len(self.collection)

    def insert(self, data: List[EntryResource]) -> None:
        raise NotImplementedError

    def count(self, *, filter, skip=0, limit=INF) -> int:
        filter_function = create_filter_function(filter)
        return self.collection.count(filter_function, skip=skip, limit=limit)

    def _run_db_query(
        self, criteria: Dict[str, Any], single_entry: bool = False
    ) -> Tuple[List[Dict[str, Any]], int, bool]:

        filter_function = create_filter_function(criteria["filter"])

        ids = [
            row.id
            for row in self.collection.select(
                filter_function, skip=criteria.get("skip", 0)
            )
        ]

        results = [self.collection.get_result(id) for id in ids[: criteria["limit"]]]

        if single_entry:
            data_returned = len(results)
            more_data_available = False
        else:
            data_returned = len(ids)
            more_data_available = data_returned > len(results)

        return results, data_returned, more_data_available


class RowInfo(NamedTuple):
    """Summary of a row in a real ASE database (used for search)."""

    id: int
    elements: Dict[str, int]
    chemical_formula_hill: str
    chemical_formula_abc: str
    nsites: int


FilterFunction = Callable[[RowInfo], bool]


def dbrow2rowinfo(row: AtomsRow) -> RowInfo:
    """Pull out stuff needed for search."""
    formula = Formula(row.formula)
    rowinfo = RowInfo(
        row.id, row.count_atoms(), f"{formula:hill}", f"{formula:abc}", row.natoms
    )

    return rowinfo


class ASEDBWrapper:
    def __init__(self, db_filename: str):
        """Search interface for ASE database."""
        self.db = connect(db_filename)
        self.rows = [dbrow2rowinfo(dbrow) for dbrow in self.db.select()]

    def __len__(self):
        return len(self.rows)

    def select(
        self, filter_function: FilterFunction, skip: int = 0, limit: int = INF
    ) -> Generator[RowInfo, None, None]:
        """Select rows using a filter function."""
        for i, row in enumerate(self.rows):
            if i == skip + limit:
                return
            if i >= skip and filter_function(row):
                yield row

    def count(self, filter_function, skip=0, limit=INF):
        return sum(1 for _ in self.select(filter_function, skip=skip, limit=limit))

    def get_result(self, id: int) -> Dict[str, Any]:
        row = self.db.get(id=id)
        count = dict(sorted(row.count_atoms().items()))
        formula = Formula.from_dict(count)
        abc, _, N = formula.stoichiometry()
        anonymous = dict2str({symb: n * N for symb, n in abc._count.items()})
        t = row.mtime * YEAR + T2000
        last_modified = strftime("%Y-%m-%dT%H:%M:%SZ", gmtime(t))
        dct = {
            "cartesian_site_positions": row.positions.tolist(),
            "species_at_sites": row.symbols,
            "nsites": row.natoms,
            "species": [
                {"name": symbol, "chemical_symbols": [symbol], "concentration": [1.0]}
                for symbol in count
            ],
            "lattice_vectors": row.cell.tolist(),
            "dimension_types": row.pbc.astype(int).tolist(),
            "last_modified": last_modified,
            "elements": list(count),
            "nelements": len(count),
            "elements_ratios": [n / row.natoms for n in count.values()],
            "chemical_formula_descriptive": "x",
            "chemical_formula_reduced": f"{formula}",
            "chemical_formula_hill": f"{formula:hill}",
            "chemical_formula_anonymous": anonymous,
            "nperiodic_dimensions": sum(row.pbc),
            "structure_features": [],
            "id": str(row.id),
        }

        return dct


def create_code_string(query: ASEQueryTree) -> str:
    """Convert query-tree object to a Python function.

    Example:

    >>> tree = ('AND', [('nelements', ('=', 3)),
    ...                 ('elements', ('HAS', '"Cu"'))])
    >>> create_code_string(tree)
    <function <lambda> at 0x7f6d5bad6ca0>
    """

    q1, q2 = query

    if q1 == "AND":
        return " and ".join(f"({create_code_string(q)})" for q in q2)

    if q1 == "nelements":
        op, val = q2
        if op == "=":
            op = "=="
        return f"len(row.elements) {op} {val}"

    if q1 == "elements":
        q3, q4 = q2

        if q3 == "HAS":
            return f"{q4} in row.elements"

        if q3 == "HAS ALL":
            return f"all(symbol in row.elements for symbol in {q4})"

    raise NotImplementedError(query)


@lru_cache(maxsize=100)
def create_filter_function(query: ASEQueryTree) -> FilterFunction:
    """Convert query-tree from ASETransofmer to a Python filter-function."""
    code_string = create_code_string(query)
    code = compile("lambda row: " + code_string, "<string>", "eval")
    filter_function = eval(code)
    return filter_function
