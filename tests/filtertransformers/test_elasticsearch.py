import pytest


elasticsearch_dsl = pytest.importorskip(
    "elasticsearch_dsl", reason="No ElasticSearch installation, skipping tests..."
)

from optimade.filterparser import LarkParser
from optimade.filtertransformers.elasticsearch import ElasticTransformer, Quantity


@pytest.fixture
def parser():
    return LarkParser(version=(0, 10, 1))


@pytest.fixture
def transformer():
    nelements = Quantity(name="nelements")
    elements_only = Quantity(name="elements_only")
    elements_ratios = Quantity(name="elements_ratios")
    elements_ratios.nested_quantity = elements_ratios
    elements = Quantity(
        name="elements",
        length_quantity=nelements,
        has_only_quantity=elements_only,
        nested_quantity=elements_ratios,
    )
    dimension_types = Quantity(name="dimension_types")
    dimension_types.length_quantity = dimension_types

    quantities = [
        nelements,
        elements_only,
        elements_ratios,
        elements,
        dimension_types,
        Quantity(name="chemical_formula_reduced"),
    ]
    return ElasticTransformer(quantities=quantities)


test_queries = [
    ("nelements > 1", 4),
    ("nelements >= 2", 4),
    ("nelements > 2", 1),
    ("nelements < 4", 4),
    ("nelements < 3", 3),
    ("nelements <= 3", 4),
    ("nelements != 2", 1),
    ("1 < nelements", 4),
    ('elements HAS "H"', 4),
    ('elements HAS ALL "H", "O"', 4),
    ('elements HAS ALL "H", "C"', 1),
    ('elements HAS ANY "H", "C"', 4),
    ('elements HAS ANY "C"', 1),
    ('elements HAS ONLY "C"', 0),
    ('elements HAS ONLY "H", "O"', 3),
    ('elements:elements_ratios HAS "H":>0.66', 2),
    ('elements:elements_ratios HAS ALL "O":>0.33', 3),
    ('elements:elements_ratios HAS ALL "O":>0.33,"O":<0.34', 2),
    ("elements IS KNOWN", 4),
    ("elements IS UNKNOWN", 0),
    ('chemical_formula_reduced = "H2O"', 2),
    ('chemical_formula_reduced CONTAINS "H2"', 3),
    ('chemical_formula_reduced CONTAINS "H"', 4),
    ('chemical_formula_reduced CONTAINS "C"', 1),
    ('chemical_formula_reduced STARTS "H2"', 3),
    ('chemical_formula_reduced STARTS WITH "H2"', 3),
    ('chemical_formula_reduced ENDS WITH "C"', 1),
    ('chemical_formula_reduced ENDS "C"', 1),
    ("elements LENGTH = 2", 3),
    ("elements LENGTH = 3", 1),
    ("dimension_types LENGTH = 0", 3),
    ("dimension_typesLENGTH = 1", 1),
    ("nelements = 2 AND dimension_types LENGTH = 1", 1),
    ("nelements = 3 AND dimension_types LENGTH = 1", 0),
    ("nelements = 3 OR dimension_types LENGTH = 1", 2),
    ("nelements > 1 OR dimension_types LENGTH = 1 AND nelements = 2", 4),
    ("(nelements > 1 OR dimension_types LENGTH = 1) AND nelements = 2", 3),
    ("NOT dimension_types LENGTH = 1", 3),
]


@pytest.mark.parametrize("query", test_queries)
def test_parse_n_transform(query, parser, transformer):
    tree = parser.parse(query[0])
    result = transformer.transform(tree)
    assert result is not None
