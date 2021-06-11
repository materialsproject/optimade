import inspect
import warnings
import re
import itertools
from enum import Enum
from typing import Optional

from pydantic import Field

_PYDANTIC_FIELD_KWARGS = list(inspect.signature(Field).parameters.keys())

__all__ = (
    "CHEMICAL_SYMBOLS",
    "EXTRA_SYMBOLS",
    "ATOMIC_NUMBERS",
    "SemanticVersion",
    "SupportLevel",
)


class SupportLevel(Enum):
    """OPTIMADE property/field support levels"""

    MUST = "must"
    SHOULD = "should"
    OPTIONAL = "optional"


def StrictField(
    *args,
    description: str = None,
    **kwargs,
) -> Field:
    """A wrapper around `pydantic.Field` that does the following:

    - Forbids any "extra" keys that would be passed to `pydantic.Field`,
      except those used elsewhere to modify the schema in-place,
      e.g. "uniqueItems", "pattern" and those added by OptimadeField, e.g.
      "unit", "queryable" and "sortable".
    - Emits a warning when no description is provided.

    Arguments:
        *args: Positional arguments passed through to `Field`.
        description: The description of the `Field`; if this is not
            specified then a `UserWarning` will be emitted.
        **kwargs: Extra keyword arguments to be passed to `Field`.

    Raises:
        RuntimeError: If `**kwargs` contains a key not found in the
            function signature of `Field`, or in the extensions used
            by models in this package (see above).

    Returns:
        The pydantic `Field`.

    """

    allowed_keys = [
        "unit",
        "pattern",
        "uniqueItems",
        "support",
        "queryable",
        "sortable",
    ]
    _banned = [k for k in kwargs if k not in set(_PYDANTIC_FIELD_KWARGS + allowed_keys)]

    if _banned:
        raise RuntimeError(
            f"Not creating StrictField({args}, {kwargs}) with forbidden keywords {_banned}."
        )

    if description is not None:
        kwargs["description"] = description

    if description is None:
        warnings.warn(
            f"No description provided for StrictField specified by {args}, {kwargs}."
        )

    return Field(*args, **kwargs)


def OptimadeField(
    *args,
    support: Optional[SupportLevel] = None,
    queryable: Optional[SupportLevel] = None,
    unit: Optional[str] = None,
    **kwargs,
) -> Field:
    """A wrapper around `pydantic.Field` that adds OPTIMADE-specific
    field paramters `queryable`, `support` and `unit`, indicating
    the corresponding support level in the specification and the
    physical unit of the field.

    Arguments:
        support: The support level of the field itself, i.e. whether the field
            can be null or omitted by an implementation.
        queryable: The support level corresponding to the queryablility
            of this field.
        unit: A string describing the unit of the field.

    Returns:
        The pydantic field with extra validation provided by [`StrictField`][optimade.models.utils.StrictField].

    """

    # Collect non-null keyword arguments to add to the Field schema
    if unit is not None:
        kwargs["unit"] = unit
    if queryable is not None:
        if isinstance(queryable, str):
            queryable = SupportLevel(queryable.lower())
        kwargs["queryable"] = queryable
    if support is not None:
        if isinstance(support, str):
            support = SupportLevel(support.lower())
        kwargs["support"] = support

    return StrictField(*args, **kwargs)


class SemanticVersion(str):
    """A custom type for a semantic version, using the recommended
    semver regexp from
    https://semver.org/#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string.

    """

    regex = re.compile(
        r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
    )

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(
            pattern=cls.regex.pattern,
            examples=["0.10.1", "1.0.0-rc.2", "1.2.3-rc.5+develop"],
        )

    @classmethod
    def validate(cls, v: str):
        if not cls.regex.match(v):
            raise ValueError(
                f"Unable to validate the version string {v!r} as a semantic version (expected <major>.<minor>.<patch>)."
                "See https://semver.org/#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string for more information."
            )

        return v

    @property
    def _match(self):
        """The result of the regex match."""
        return self.regex.match(self)

    @property
    def major(self) -> int:
        """The major version number."""
        return int(self._match.group(1))

    @property
    def minor(self) -> int:
        """The minor version number."""
        return int(self._match.group(2))

    @property
    def patch(self) -> int:
        """The patch version number."""
        return int(self._match.group(3))

    @property
    def prerelease(self) -> str:
        """The pre-release tag."""
        return self._match.group(4)

    @property
    def build_metadata(self) -> str:
        """The build metadata."""
        return self._match.group(5)

    @property
    def base_version(self) -> str:
        """The base version string without patch and metadata info."""
        return f"{self.major}.{self.minor}.{self.patch}"


def anonymous_element_generator():
    """Generator that yields the next symbol in the A, B, Aa, ... Az naming scheme."""
    from string import ascii_lowercase

    for size in itertools.count(1):
        for s in itertools.product(ascii_lowercase, repeat=size):
            s = list(s)
            s[0] = s[0].upper()
            yield "".join(s)


ANONYMOUS_ELEMENTS = tuple(itertools.islice(anonymous_element_generator(), 150))
""" Returns the first 150 values of the anonymous element generator. """

CHEMICAL_FORMULA_REGEXP = r"^([A-Z][a-z]?\d*)*$"

EXTRA_SYMBOLS = ["X", "vacancy"]

CHEMICAL_SYMBOLS = [
    "H",
    "He",
    "Li",
    "Be",
    "B",
    "C",
    "N",
    "O",
    "F",
    "Ne",
    "Na",
    "Mg",
    "Al",
    "Si",
    "P",
    "S",
    "Cl",
    "Ar",
    "K",
    "Ca",
    "Sc",
    "Ti",
    "V",
    "Cr",
    "Mn",
    "Fe",
    "Co",
    "Ni",
    "Cu",
    "Zn",
    "Ga",
    "Ge",
    "As",
    "Se",
    "Br",
    "Kr",
    "Rb",
    "Sr",
    "Y",
    "Zr",
    "Nb",
    "Mo",
    "Tc",
    "Ru",
    "Rh",
    "Pd",
    "Ag",
    "Cd",
    "In",
    "Sn",
    "Sb",
    "Te",
    "I",
    "Xe",
    "Cs",
    "Ba",
    "La",
    "Ce",
    "Pr",
    "Nd",
    "Pm",
    "Sm",
    "Eu",
    "Gd",
    "Tb",
    "Dy",
    "Ho",
    "Er",
    "Tm",
    "Yb",
    "Lu",
    "Hf",
    "Ta",
    "W",
    "Re",
    "Os",
    "Ir",
    "Pt",
    "Au",
    "Hg",
    "Tl",
    "Pb",
    "Bi",
    "Po",
    "At",
    "Rn",
    "Fr",
    "Ra",
    "Ac",
    "Th",
    "Pa",
    "U",
    "Np",
    "Pu",
    "Am",
    "Cm",
    "Bk",
    "Cf",
    "Es",
    "Fm",
    "Md",
    "No",
    "Lr",
    "Rf",
    "Db",
    "Sg",
    "Bh",
    "Hs",
    "Mt",
    "Ds",
    "Rg",
    "Cn",
    "Nh",
    "Fl",
    "Mc",
    "Lv",
    "Ts",
    "Og",
]

ATOMIC_NUMBERS = {}
for Z, symbol in enumerate(CHEMICAL_SYMBOLS):
    ATOMIC_NUMBERS[symbol] = Z + 1
