# pylint: disable=no-self-argument,line-too-long,no-name-in-module
import re
import warnings
from enum import IntEnum, Enum
from sys import float_info
from typing import List, Optional, Union

from pydantic import BaseModel, validator, root_validator, conlist

from optimade.models.entries import EntryResourceAttributes, EntryResource
from optimade.models.utils import (
    CHEMICAL_SYMBOLS,
    EXTRA_SYMBOLS,
    OptimadeField,
    StrictField,
    SupportLevel,
    ANONYMOUS_ELEMENTS,
    CHEMICAL_FORMULA_REGEXP,
)
from optimade.server.warnings import MissingExpectedField

EXTENDED_CHEMICAL_SYMBOLS = CHEMICAL_SYMBOLS + EXTRA_SYMBOLS


__all__ = (
    "Vector3D",
    "Periodicity",
    "StructureFeatures",
    "Species",
    "Assembly",
    "StructureResourceAttributes",
    "StructureResource",
)


EPS = float_info.epsilon


Vector3D = conlist(float, min_items=3, max_items=3)
Vector3D_unknown = conlist(Union[float, None], min_items=3, max_items=3)


class Periodicity(IntEnum):
    """Integer enumeration of dimension_types values"""

    APERIODIC = 0
    PERIODIC = 1


class StructureFeatures(Enum):
    """Enumeration of structure_features values"""

    DISORDER = "disorder"
    IMPLICIT_ATOMS = "implicit_atoms"
    SITE_ATTACHMENTS = "site_attachments"
    ASSEMBLIES = "assemblies"


class Species(BaseModel):
    """A list describing the species of the sites of this structure.

    Species can represent pure chemical elements, virtual-crystal atoms representing a
    statistical occupation of a given site by multiple chemical elements, and/or a
    location to which there are attached atoms, i.e., atoms whose precise location are
    unknown beyond that they are attached to that position (frequently used to indicate
    hydrogen atoms attached to another element, e.g., a carbon with three attached
    hydrogens might represent a methyl group, -CH3).

    - **Examples**:
        - `[ {"name": "Ti", "chemical_symbols": ["Ti"], "concentration": [1.0]} ]`: any site with this species is occupied by a Ti atom.
        - `[ {"name": "Ti", "chemical_symbols": ["Ti", "vacancy"], "concentration": [0.9, 0.1]} ]`: any site with this species is occupied by a Ti atom with 90 % probability, and has a vacancy with 10 % probability.
        - `[ {"name": "BaCa", "chemical_symbols": ["vacancy", "Ba", "Ca"], "concentration": [0.05, 0.45, 0.5], "mass": [0.0, 137.327, 40.078]} ]`: any site with this species is occupied by a Ba atom with 45 % probability, a Ca atom with 50 % probability, and by a vacancy with 5 % probability. The mass of this site is (on average) 88.5 a.m.u.
        - `[ {"name": "C12", "chemical_symbols": ["C"], "concentration": [1.0], "mass": [12.0]} ]`: any site with this species is occupied by a carbon isotope with mass 12.
        - `[ {"name": "C13", "chemical_symbols": ["C"], "concentration": [1.0], "mass": [13.0]} ]`: any site with this species is occupied by a carbon isotope with mass 13.
        - `[ {"name": "CH3", "chemical_symbols": ["C"], "concentration": [1.0], "attached": ["H"], "nattached": [3]} ]`: any site with this species is occupied by a methyl group, -CH3, which is represented without specifying precise positions of the hydrogen atoms.

    """

    name: str = OptimadeField(
        ...,
        description="""Gives the name of the species; the **name** value MUST be unique in the `species` list.""",
        support=SupportLevel.MUST,
        queryable=SupportLevel.OPTIONAL,
    )

    chemical_symbols: List[str] = OptimadeField(
        ...,
        description="""MUST be a list of strings of all chemical elements composing this species. Each item of the list MUST be one of the following:

- a valid chemical-element name, or
- the special value `"X"` to represent a non-chemical element, or
- the special value `"vacancy"` to represent that this site has a non-zero probability of having a vacancy (the respective probability is indicated in the `concentration` list, see below).

If any one entry in the `species` list has a `chemical_symbols` list that is longer than 1 element, the correct flag MUST be set in the list `structure_features`.""",
        support=SupportLevel.MUST,
        queryable=SupportLevel.OPTIONAL,
    )

    concentration: List[float] = OptimadeField(
        ...,
        description="""MUST be a list of floats, with same length as `chemical_symbols`. The numbers represent the relative concentration of the corresponding chemical symbol in this species. The numbers SHOULD sum to one. Cases in which the numbers do not sum to one typically fall only in the following two categories:

- Numerical errors when representing float numbers in fixed precision, e.g. for two chemical symbols with concentrations `1/3` and `2/3`, the concentration might look something like `[0.33333333333, 0.66666666666]`. If the client is aware that the sum is not one because of numerical precision, it can renormalize the values so that the sum is exactly one.
- Experimental errors in the data present in the database. In this case, it is the responsibility of the client to decide how to process the data.

Note that concentrations are uncorrelated between different site (even of the same species).""",
        support=SupportLevel.MUST,
        queryable=SupportLevel.OPTIONAL,
    )

    mass: Optional[List[float]] = OptimadeField(
        None,
        description="""If present MUST be a list of floats expressed in a.m.u.
Elements denoting vacancies MUST have masses equal to 0.""",
        unit="a.m.u.",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )

    original_name: Optional[str] = OptimadeField(
        None,
        description="""Can be any valid Unicode string, and SHOULD contain (if specified) the name of the species that is used internally in the source database.

Note: With regards to "source database", we refer to the immediate source being queried via the OPTIMADE API implementation.""",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )

    attached: Optional[List[str]] = OptimadeField(
        None,
        description="""If provided MUST be a list of length 1 or more of strings of chemical symbols for the elements attached to this site, or "X" for a non-chemical element.""",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )

    nattached: Optional[List[int]] = OptimadeField(
        None,
        description="""If provided MUST be a list of length 1 or more of integers indicating the number of attached atoms of the kind specified in the value of the :field:`attached` key.""",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )

    @validator("chemical_symbols", each_item=True)
    def validate_chemical_symbols(cls, v):
        if not (v in EXTENDED_CHEMICAL_SYMBOLS):
            raise ValueError(f"{v} MUST be in {EXTENDED_CHEMICAL_SYMBOLS}")
        return v

    @validator("concentration", "mass")
    def validate_concentration_and_mass(cls, v, values, field):
        if not v:
            return v
        if values.get("chemical_symbols"):
            if len(v) != len(values["chemical_symbols"]):
                raise ValueError(
                    f"Length of concentration ({len(v)}) MUST equal length of chemical_symbols "
                    f"({len(values.get('chemical_symbols', []))})"
                )
            return v

        raise ValueError(
            "Could not validate {field.name} as 'chemical_symbols' is missing/invalid."
        )

    @validator("attached", "nattached")
    def validate_minimum_list_length(cls, v):
        if v is not None and len(v) < 1:
            raise ValueError(
                f"The list's length MUST be 1 or more, instead it was found to be {len(v)}"
            )
        return v

    @root_validator
    def attached_nattached_mutually_exclusive(cls, values):
        attached, nattached = (
            values.get("attached", None),
            values.get("nattached", None),
        )
        if (attached is None and nattached is not None) or (
            attached is not None and nattached is None
        ):
            raise ValueError(
                f"Either both or none of attached ({attached}) and nattached ({nattached}) MUST be set."
            )

        if (
            attached is not None
            and nattached is not None
            and len(attached) != len(nattached)
        ):
            raise ValueError(
                f"attached ({attached}) and nattached ({nattached}) MUST be lists of equal length."
            )

        return values


class Assembly(BaseModel):
    """A description of groups of sites that are statistically correlated.

    - **Examples** (for each entry of the assemblies list):
        - `{"sites_in_groups": [[0], [1]], "group_probabilities: [0.3, 0.7]}`: the first site and the second site never occur at the same time in the unit cell.
          Statistically, 30 % of the times the first site is present, while 70 % of the times the second site is present.
        - `{"sites_in_groups": [[1,2], [3]], "group_probabilities: [0.3, 0.7]}`: the second and third site are either present together or not present; they form the first group of atoms for this assembly.
          The second group is formed by the fourth site. Sites of the first group (the second and the third) are never present at the same time as the fourth site.
          30 % of times sites 1 and 2 are present (and site 3 is absent); 70 % of times site 3 is present (and sites 1 and 2 are absent).

    """

    sites_in_groups: List[List[int]] = OptimadeField(
        ...,
        description="""Index of the sites (0-based) that belong to each group for each assembly.

- **Examples**:
    - `[[1], [2]]`: two groups, one with the second site, one with the third.
    - `[[1,2], [3]]`: one group with the second and third site, one with the fourth.""",
        support=SupportLevel.MUST,
        queryable=SupportLevel.OPTIONAL,
    )

    group_probabilities: List[float] = OptimadeField(
        ...,
        description="""Statistical probability of each group. It MUST have the same length as `sites_in_groups`.
It SHOULD sum to one.
See below for examples of how to specify the probability of the occurrence of a vacancy.
The possible reasons for the values not to sum to one are the same as already specified above for the `concentration` of each `species`.""",
        support=SupportLevel.MUST,
        queryable=SupportLevel.OPTIONAL,
    )

    @validator("sites_in_groups")
    def validate_sites_in_groups(cls, v):
        sites = []
        for group in v:
            sites.extend(group)
        if len(set(sites)) != len(sites):
            raise ValueError(
                f"A site MUST NOT appear in more than one group. Given value: {v}"
            )
        return v

    @validator("group_probabilities")
    def check_self_consistency(cls, v, values):
        if len(v) != len(values.get("sites_in_groups", [])):
            raise ValueError(
                f"sites_in_groups and group_probabilities MUST be of same length, "
                f"but are {len(values.get('sites_in_groups', []))} and {len(v)}, respectively"
            )
        return v


CORRELATED_STRUCTURE_FIELDS = (
    {"dimension_types", "nperiodic_dimensions"},
    {"cartesian_site_positions", "species_at_sites"},
    {"nsites", "cartesian_site_positions"},
    {"species_at_sites", "species"},
)


class StructureResourceAttributes(EntryResourceAttributes):
    """This class contains the Field for the attributes used to represent a structure, e.g. unit cell, atoms, positions."""

    elements: Optional[List[str]] = OptimadeField(
        ...,
        description="""Names of the different elements present in the structure.

- **Type**: list of strings.

- **Requirements/Conventions**:
    - **Support**: SHOULD be supported by all implementations, i.e., SHOULD NOT be `null`.
    - **Query**: MUST be a queryable property with support for all mandatory filter features.
    - The strings are the chemical symbols, i.e., either a single uppercase letter or an uppercase letter followed by a number of lowercase letters.
    - The order MUST be alphabetical.
    - MUST refer to the same elements in the same order, and therefore be of the same length, as `elements_ratios`, if the latter is provided.
    - Note: This property SHOULD NOT contain the string "X" to indicate non-chemical elements or "vacancy" to indicate vacancies (in contrast to the field `chemical_symbols` for the `species` property).

- **Examples**:
    - `["Si"]`
    - `["Al","O","Si"]`

- **Query examples**:
    - A filter that matches all records of structures that contain Si, Al **and** O, and possibly other elements: `elements HAS ALL "Si", "Al", "O"`.
    - To match structures with exactly these three elements, use `elements HAS ALL "Si", "Al", "O" AND elements LENGTH 3`.
    - Note: length queries on this property can be equivalently formulated by filtering on the `nelements`_ property directly.""",
        support=SupportLevel.SHOULD,
        queryable=SupportLevel.MUST,
    )

    nelements: Optional[int] = OptimadeField(
        ...,
        description="""Number of different elements in the structure as an integer.

- **Type**: integer

- **Requirements/Conventions**:
    - **Support**: SHOULD be supported by all implementations, i.e., SHOULD NOT be `null`.
    - **Query**: MUST be a queryable property with support for all mandatory filter features.
    - MUST be equal to the lengths of the list properties `elements` and `elements_ratios`, if they are provided.

- **Examples**:
    - `3`

- **Querying**:
    - Note: queries on this property can equivalently be formulated using `elements LENGTH`.
    - A filter that matches structures that have exactly 4 elements: `nelements=4`.
    - A filter that matches structures that have between 2 and 7 elements: `nelements>=2 AND nelements<=7`.""",
        support=SupportLevel.SHOULD,
        queryable=SupportLevel.MUST,
    )

    elements_ratios: Optional[List[float]] = OptimadeField(
        ...,
        description="""Relative proportions of different elements in the structure.

- **Type**: list of floats

- **Requirements/Conventions**:
    - **Support**: SHOULD be supported by all implementations, i.e., SHOULD NOT be `null`.
    - **Query**: MUST be a queryable property with support for all mandatory filter features.
    - Composed by the proportions of elements in the structure as a list of floating point numbers.
    - The sum of the numbers MUST be 1.0 (within floating point accuracy)
    - MUST refer to the same elements in the same order, and therefore be of the same length, as `elements`, if the latter is provided.

- **Examples**:
    - `[1.0]`
    - `[0.3333333333333333, 0.2222222222222222, 0.4444444444444444]`

- **Query examples**:
    - Note: Useful filters can be formulated using the set operator syntax for correlated values.
      However, since the values are floating point values, the use of equality comparisons is generally inadvisable.
    - OPTIONAL: a filter that matches structures where approximately 1/3 of the atoms in the structure are the element Al is: `elements:elements_ratios HAS ALL "Al":>0.3333, "Al":<0.3334`.""",
        support=SupportLevel.SHOULD,
        queryable=SupportLevel.MUST,
    )

    chemical_formula_descriptive: Optional[str] = OptimadeField(
        ...,
        description="""The chemical formula for a structure as a string in a form chosen by the API implementation.

- **Type**: string

- **Requirements/Conventions**:
    - **Support**: SHOULD be supported by all implementations, i.e., SHOULD NOT be `null`.
    - **Query**: MUST be a queryable property with support for all mandatory filter features.
    - The chemical formula is given as a string consisting of properly capitalized element symbols followed by integers or decimal numbers, balanced parentheses, square, and curly brackets `(`,`)`, `[`,`]`, `{`, `}`, commas, the `+`, `-`, `:` and `=` symbols. The parentheses are allowed to be followed by a number. Spaces are allowed anywhere except within chemical symbols. The order of elements and any groupings indicated by parentheses or brackets are chosen freely by the API implementation.
    - The string SHOULD be arithmetically consistent with the element ratios in the `chemical_formula_reduced` property.
    - It is RECOMMENDED, but not mandatory, that symbols, parentheses and brackets, if used, are used with the meanings prescribed by [IUPAC's Nomenclature of Organic Chemistry](https://www.qmul.ac.uk/sbcs/iupac/bibliog/blue.html).

- **Examples**:
    - `"(H2O)2 Na"`
    - `"NaCl"`
    - `"CaCO3"`
    - `"CCaO3"`
    - `"(CH3)3N+ - [CH2]2-OH = Me3N+ - CH2 - CH2OH"`

- **Query examples**:
    - Note: the free-form nature of this property is likely to make queries on it across different databases inconsistent.
    - A filter that matches an exactly given formula: `chemical_formula_descriptive="(H2O)2 Na"`.
    - A filter that does a partial match: `chemical_formula_descriptive CONTAINS "H2O"`.""",
        support=SupportLevel.SHOULD,
        queryable=SupportLevel.MUST,
    )

    chemical_formula_reduced: Optional[str] = OptimadeField(
        ...,
        description="""The reduced chemical formula for a structure as a string with element symbols and integer chemical proportion numbers.
The proportion number MUST be omitted if it is 1.

- **Type**: string

- **Requirements/Conventions**:
    - **Support**: SHOULD be supported by all implementations, i.e., SHOULD NOT be `null`.
    - **Query**: MUST be a queryable property.
      However, support for filters using partial string matching with this property is OPTIONAL (i.e., BEGINS WITH, ENDS WITH, and CONTAINS).
      Intricate queries on formula components are instead suggested to be formulated using set-type filter operators on the multi valued `elements` and `elements_ratios` properties.
    - Element names MUST have proper capitalization (e.g., `"Si"`, not `"SI"` for "silicon").
    - Elements MUST be placed in alphabetical order, followed by their integer chemical proportion number.
    - For structures with no partial occupation, the chemical proportion numbers are the smallest integers for which the chemical proportion is exactly correct.
    - For structures with partial occupation, the chemical proportion numbers are integers that within reasonable approximation indicate the correct chemical proportions. The precise details of how to perform the rounding is chosen by the API implementation.
    - No spaces or separators are allowed.

- **Examples**:
    - `"H2NaO"`
    - `"ClNa"`
    - `"CCaO3"`

- **Query examples**:
    - A filter that matches an exactly given formula is `chemical_formula_reduced="H2NaO"`.""",
        support=SupportLevel.SHOULD,
        queryable=SupportLevel.MUST,
        regex=CHEMICAL_FORMULA_REGEXP,
    )

    chemical_formula_hill: Optional[str] = OptimadeField(
        None,
        description="""The chemical formula for a structure in [Hill form](https://dx.doi.org/10.1021/ja02046a005) with element symbols followed by integer chemical proportion numbers. The proportion number MUST be omitted if it is 1.

- **Type**: string

- **Requirements/Conventions**:
    - **Support**: OPTIONAL support in implementations, i.e., MAY be `null`.
    - **Query**: Support for queries on this property is OPTIONAL.
      If supported, only a subset of the filter features MAY be supported.
    - The overall scale factor of the chemical proportions is chosen such that the resulting values are integers that indicate the most chemically relevant unit of which the system is composed.
      For example, if the structure is a repeating unit cell with four hydrogens and four oxygens that represents two hydroperoxide molecules, `chemical_formula_hill` is `"H2O2"` (i.e., not `"HO"`, nor `"H4O4"`).
    - If the chemical insight needed to ascribe a Hill formula to the system is not present, the property MUST be handled as unset.
    - Element names MUST have proper capitalization (e.g., `"Si"`, not `"SI"` for "silicon").
    - Elements MUST be placed in [Hill order](https://dx.doi.org/10.1021/ja02046a005), followed by their integer chemical proportion number.
      Hill order means: if carbon is present, it is placed first, and if also present, hydrogen is placed second.
      After that, all other elements are ordered alphabetically.
      If carbon is not present, all elements are ordered alphabetically.
    - If the system has sites with partial occupation and the total occupations of each element do not all sum up to integers, then the Hill formula SHOULD be handled as unset.
    - No spaces or separators are allowed.

- **Examples**:
    - `"H2O2"`

- **Query examples**:
    - A filter that matches an exactly given formula is `chemical_formula_hill="H2O2"`.""",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
        regex=CHEMICAL_FORMULA_REGEXP,
    )

    chemical_formula_anonymous: Optional[str] = OptimadeField(
        ...,
        description="""The anonymous formula is the `chemical_formula_reduced`, but where the elements are instead first ordered by their chemical proportion number, and then, in order left to right, replaced by anonymous symbols A, B, C, ..., Z, Aa, Ba, ..., Za, Ab, Bb, ... and so on.

- **Type**: string

- **Requirements/Conventions**:
    - **Support**: SHOULD be supported by all implementations, i.e., SHOULD NOT be `null`.
    - **Query**: MUST be a queryable property.
      However, support for filters using partial string matching with this property is OPTIONAL (i.e., BEGINS WITH, ENDS WITH, and CONTAINS).

- **Examples**:
    - `"A2B"`
    - `"A42B42C16D12E10F9G5"`

- **Querying**:
    - A filter that matches an exactly given formula is `chemical_formula_anonymous="A2B"`.""",
        support=SupportLevel.SHOULD,
        queryable=SupportLevel.MUST,
        regex=CHEMICAL_FORMULA_REGEXP,
    )

    dimension_types: Optional[
        conlist(Periodicity, min_items=3, max_items=3)
    ] = OptimadeField(
        None,
        title="Dimension Types",
        description="""List of three integers.
For each of the three directions indicated by the three lattice vectors (see property `lattice_vectors`), this list indicates if the direction is periodic (value `1`) or non-periodic (value `0`).
Note: the elements in this list each refer to the direction of the corresponding entry in `lattice_vectors` and *not* the Cartesian x, y, z directions.

- **Type**: list of integers.

- **Requirements/Conventions**:
    - **Support**: SHOULD be supported by all implementations, i.e., SHOULD NOT be `null`.
    - **Query**: Support for queries on this property is OPTIONAL.
    - MUST be a list of length 3.
    - Each integer element MUST assume only the value 0 or 1.

- **Examples**:
    - For a molecule: `[0, 0, 0]`
    - For a wire along the direction specified by the third lattice vector: `[0, 0, 1]`
    - For a 2D surface/slab, periodic on the plane defined by the first and third lattice vectors: `[1, 0, 1]`
    - For a bulk 3D system: `[1, 1, 1]`""",
        support=SupportLevel.SHOULD,
        queryable=SupportLevel.OPTIONAL,
    )

    nperiodic_dimensions: Optional[int] = OptimadeField(
        ...,
        description="""An integer specifying the number of periodic dimensions in the structure, equivalent to the number of non-zero entries in `dimension_types`.

- **Type**: integer

- **Requirements/Conventions**:
    - **Support**: SHOULD be supported by all implementations, i.e., SHOULD NOT be `null`.
    - **Query**: MUST be a queryable property with support for all mandatory filter features.
    - The integer value MUST be between 0 and 3 inclusive and MUST be equal to the sum of the items in the `dimension_types` property.
    - This property only reflects the treatment of the lattice vectors provided for the structure, and not any physical interpretation of the dimensionality of its contents.

- **Examples**:
    - `2` should be indicated in cases where `dimension_types` is any of `[1, 1, 0]`, `[1, 0, 1]`, `[0, 1, 1]`.

- **Query examples**:
    - Match only structures with exactly 3 periodic dimensions: `nperiodic_dimensions=3`
    - Match all structures with 2 or fewer periodic dimensions: `nperiodic_dimensions<=2`""",
        support=SupportLevel.SHOULD,
        queryable=SupportLevel.MUST,
    )

    lattice_vectors: Optional[
        conlist(Vector3D_unknown, min_items=3, max_items=3)
    ] = OptimadeField(
        None,
        description="""The three lattice vectors in Cartesian coordinates, in ångström (Å).

- **Type**: list of list of floats or unknown values.

- **Requirements/Conventions**:
    - **Support**: SHOULD be supported by all implementations, i.e., SHOULD NOT be `null`.
    - **Query**: Support for queries on this property is OPTIONAL.
      If supported, filters MAY support only a subset of comparison operators.
    - MUST be a list of three vectors *a*, *b*, and *c*, where each of the vectors MUST BE a list of the vector's coordinates along the x, y, and z Cartesian coordinates.
      (Therefore, the first index runs over the three lattice vectors and the second index runs over the x, y, z Cartesian coordinates).
    - For databases that do not define an absolute Cartesian system (e.g., only defining the length and angles between vectors), the first lattice vector SHOULD be set along *x* and the second on the *xy*-plane.
    - MUST always contain three vectors of three coordinates each, independently of the elements of property `dimension_types`.
      The vectors SHOULD by convention be chosen so the determinant of the `lattice_vectors` matrix is different from zero.
      The vectors in the non-periodic directions have no significance beyond fulfilling these requirements.
    - The coordinates of the lattice vectors of non-periodic dimensions (i.e., those dimensions for which `dimension_types` is `0`) MAY be given as a list of all `null` values.
        If a lattice vector contains the value `null`, all coordinates of that lattice vector MUST be `null`.

- **Examples**:
    - `[[4.0,0.0,0.0],[0.0,4.0,0.0],[0.0,1.0,4.0]]` represents a cell, where the first vector is `(4, 0, 0)`, i.e., a vector aligned along the `x` axis of length 4 Å; the second vector is `(0, 4, 0)`; and the third vector is `(0, 1, 4)`.""",
        unit="Å",
        support=SupportLevel.SHOULD,
        queryable=SupportLevel.OPTIONAL,
    )

    cartesian_site_positions: Optional[List[Vector3D]] = OptimadeField(
        ...,
        description="""Cartesian positions of each site in the structure.
A site is usually used to describe positions of atoms; what atoms can be encountered at a given site is conveyed by the `species_at_sites` property, and the species themselves are described in the `species` property.

- **Type**: list of list of floats

- **Requirements/Conventions**:
    - **Support**: SHOULD be supported by all implementations, i.e., SHOULD NOT be `null`.
    - **Query**: Support for queries on this property is OPTIONAL.
      If supported, filters MAY support only a subset of comparison operators.
    - It MUST be a list of length equal to the number of sites in the structure, where every element is a list of the three Cartesian coordinates of a site expressed as float values in the unit angstrom (Å).
    - An entry MAY have multiple sites at the same Cartesian position (for a relevant use of this, see e.g., the property `assemblies`).

- **Examples**:
    - `[[0,0,0],[0,0,2]]` indicates a structure with two sites, one sitting at the origin and one along the (positive) *z*-axis, 2 Å away from the origin.""",
        unit="Å",
        support=SupportLevel.SHOULD,
        queryable=SupportLevel.OPTIONAL,
    )

    nsites: Optional[int] = OptimadeField(
        ...,
        description="""An integer specifying the length of the `cartesian_site_positions` property.

- **Type**: integer

- **Requirements/Conventions**:
    - **Support**: SHOULD be supported by all implementations, i.e., SHOULD NOT be `null`.
    - **Query**: MUST be a queryable property with support for all mandatory filter features.

- **Examples**:
    - `42`

- **Query examples**:
    - Match only structures with exactly 4 sites: `nsites=4`
    - Match structures that have between 2 and 7 sites: `nsites>=2 AND nsites<=7`""",
        queryable=SupportLevel.MUST,
        support=SupportLevel.SHOULD,
    )

    species: Optional[List[Species]] = OptimadeField(
        ...,
        description="""A list describing the species of the sites of this structure.
Species can represent pure chemical elements, virtual-crystal atoms representing a statistical occupation of a given site by multiple chemical elements, and/or a location to which there are attached atoms, i.e., atoms whose precise location are unknown beyond that they are attached to that position (frequently used to indicate hydrogen atoms attached to another element, e.g., a carbon with three attached hydrogens might represent a methyl group, -CH3).

- **Type**: list of dictionary with keys:
    - `name`: string (REQUIRED)
    - `chemical_symbols`: list of strings (REQUIRED)
    - `concentration`: list of float (REQUIRED)
    - `attached`: list of strings (REQUIRED)
    - `nattached`: list of integers (OPTIONAL)
    - `mass`: list of floats (OPTIONAL)
    - `original_name`: string (OPTIONAL).

- **Requirements/Conventions**:
    - **Support**: SHOULD be supported by all implementations, i.e., SHOULD NOT be `null`.
    - **Query**: Support for queries on this property is OPTIONAL.
        If supported, filters MAY support only a subset of comparison operators.
    - Each list member MUST be a dictionary with the following keys:
        - **name**: REQUIRED; gives the name of the species; the **name** value MUST be unique in the `species` list;
        - **chemical_symbols**: REQUIRED; MUST be a list of strings of all chemical elements composing this species.
          Each item of the list MUST be one of the following:
            - a valid chemical-element name, or
            - the special value `"X"` to represent a non-chemical element, or
            - the special value `"vacancy"` to represent that this site has a non-zero probability of having a vacancy (the respective probability is indicated in the `concentration` list, see below).

          If any one entry in the `species` list has a `chemical_symbols` list that is longer than 1 element, the correct flag MUST be set in the list `structure_features`.

        - **concentration**: REQUIRED; MUST be a list of floats, with same length as `chemical_symbols`.
          The numbers represent the relative concentration of the corresponding chemical symbol in this species.
          The numbers SHOULD sum to one. Cases in which the numbers do not sum to one typically fall only in the following two categories:

            - Numerical errors when representing float numbers in fixed precision, e.g. for two chemical symbols with concentrations `1/3` and `2/3`, the concentration might look something like `[0.33333333333, 0.66666666666]`. If the client is aware that the sum is not one because of numerical precision, it can renormalize the values so that the sum is exactly one.
            - Experimental errors in the data present in the database. In this case, it is the responsibility of the client to decide how to process the data.

            Note that concentrations are uncorrelated between different sites (even of the same species).

        - **attached**: OPTIONAL; if provided MUST be a list of length 1 or more of strings of chemical symbols for the elements attached to this site, or "X" for a non-chemical element.

        - **nattached**: OPTIONAL; if provided MUST be a list of length 1 or more of integers indicating the number of attached atoms of the kind specified in the value of the `attached` key.

          The implementation MUST include either both or none of the `attached` and `nattached` keys, and if they are provided, they MUST be of the same length.
          Furthermore, if they are provided, the `structure_features` property MUST include the string `site_attachments`.

        - **mass**: OPTIONAL. If present MUST be a list of floats, with the same length as `chemical_symbols`, providing element masses expressed in a.m.u.
          Elements denoting vacancies MUST have masses equal to 0.

        - **original_name**: OPTIONAL. Can be any valid Unicode string, and SHOULD contain (if specified) the name of the species that is used internally in the source database.

          Note: With regards to "source database", we refer to the immediate source being queried via the OPTIMADE API implementation.

          The main use of this field is for source databases that use species names, containing characters that are not allowed (see description of the list property `species_at_sites`).

    - For systems that have only species formed by a single chemical symbol, and that have at most one species per chemical symbol, SHOULD use the chemical symbol as species name (e.g., `"Ti"` for titanium, `"O"` for oxygen, etc.)
      However, note that this is OPTIONAL, and client implementations MUST NOT assume that the key corresponds to a chemical symbol, nor assume that if the species name is a valid chemical symbol, that it represents a species with that chemical symbol.
      This means that a species `{"name": "C", "chemical_symbols": ["Ti"], "concentration": [1.0]}` is valid and represents a titanium species (and *not* a carbon species).
    - It is NOT RECOMMENDED that a structure includes species that do not have at least one corresponding site.

- **Examples**:
    - `[ {"name": "Ti", "chemical_symbols": ["Ti"], "concentration": [1.0]} ]`: any site with this species is occupied by a Ti atom.
    - `[ {"name": "Ti", "chemical_symbols": ["Ti", "vacancy"], "concentration": [0.9, 0.1]} ]`: any site with this species is occupied by a Ti atom with 90 % probability, and has a vacancy with 10 % probability.
    - `[ {"name": "BaCa", "chemical_symbols": ["vacancy", "Ba", "Ca"], "concentration": [0.05, 0.45, 0.5], "mass": [0.0, 137.327, 40.078]} ]`: any site with this species is occupied by a Ba atom with 45 % probability, a Ca atom with 50 % probability, and by a vacancy with 5 % probability. The mass of this site is (on average) 88.5 a.m.u.
    - `[ {"name": "C12", "chemical_symbols": ["C"], "concentration": [1.0], "mass": [12.0]} ]`: any site with this species is occupied by a carbon isotope with mass 12.
    - `[ {"name": "C13", "chemical_symbols": ["C"], "concentration": [1.0], "mass": [13.0]} ]`: any site with this species is occupied by a carbon isotope with mass 13.
    - `[ {"name": "CH3", "chemical_symbols": ["C"], "concentration": [1.0], "attached": ["H"], "nattached": [3]} ]`: any site with this species is occupied by a methyl group, -CH3, which is represented without specifying precise positions of the hydrogen atoms.""",
        support=SupportLevel.SHOULD,
        queryable=SupportLevel.OPTIONAL,
    )

    species_at_sites: Optional[List[str]] = OptimadeField(
        ...,
        description="""Name of the species at each site (where values for sites are specified with the same order of the property `cartesian_site_positions`).
The properties of the species are found in the property `species`.

- **Type**: list of strings.

- **Requirements/Conventions**:
    - **Support**: SHOULD be supported by all implementations, i.e., SHOULD NOT be `null`.
    - **Query**: Support for queries on this property is OPTIONAL.
      If supported, filters MAY support only a subset of comparison operators.
    - MUST have length equal to the number of sites in the structure (first dimension of the list property `cartesian_site_positions`).
    - Each species name mentioned in the `species_at_sites` list MUST be described in the list property `species` (i.e. for each value in the `species_at_sites` list there MUST exist exactly one dictionary in the `species` list with the `name` attribute equal to the corresponding `species_at_sites` value).
    - Each site MUST be associated only to a single species.
      **Note**: However, species can represent mixtures of atoms, and multiple species MAY be defined for the same chemical element.
      This latter case is useful when different atoms of the same type need to be grouped or distinguished, for instance in simulation codes to assign different initial spin states.

- **Examples**:
    - `["Ti","O2"]` indicates that the first site is hosting a species labeled `"Ti"` and the second a species labeled `"O2"`.
    - `["Ac", "Ac", "Ag", "Ir"]` indicating the first two sites contains the `"Ac"` species, while the third and fourth sites contain the `"Ag"` and `"Ir"` species, respectively.""",
        support=SupportLevel.SHOULD,
        queryable=SupportLevel.OPTIONAL,
    )

    assemblies: Optional[List[Assembly]] = OptimadeField(
        None,
        description="""A description of groups of sites that are statistically correlated.

- **Type**: list of dictionary with keys:
    - `sites_in_groups`: list of list of integers (REQUIRED)
    - `group_probabilities`: list of floats (REQUIRED)

- **Requirements/Conventions**:
    - **Support**: OPTIONAL support in implementations, i.e., MAY be `null`.
    - **Query**: Support for queries on this property is OPTIONAL.
        If supported, filters MAY support only a subset of comparison operators.
    - The property SHOULD be `null` for entries that have no partial occupancies.
    - If present, the correct flag MUST be set in the list `structure_features`.
    - Client implementations MUST check its presence (as its presence changes the interpretation of the structure).
    - If present, it MUST be a list of dictionaries, each of which represents an assembly and MUST have the following two keys:
        - **sites_in_groups**: Index of the sites (0-based) that belong to each group for each assembly.

            Example: `[[1], [2]]`: two groups, one with the second site, one with the third.
            Example: `[[1,2], [3]]`: one group with the second and third site, one with the fourth.

        - **group_probabilities**: Statistical probability of each group. It MUST have the same length as `sites_in_groups`.
            It SHOULD sum to one.
            See below for examples of how to specify the probability of the occurrence of a vacancy.
            The possible reasons for the values not to sum to one are the same as already specified above for the `concentration` of each `species`.

    - If a site is not present in any group, it means that it is present with 100 % probability (as if no assembly was specified).
    - A site MUST NOT appear in more than one group.

- **Examples** (for each entry of the assemblies list):
    - `{"sites_in_groups": [[0], [1]], "group_probabilities: [0.3, 0.7]}`: the first site and the second site never occur at the same time in the unit cell.
        Statistically, 30 % of the times the first site is present, while 70 % of the times the second site is present.
    - `{"sites_in_groups": [[1,2], [3]], "group_probabilities: [0.3, 0.7]}`: the second and third site are either present together or not present; they form the first group of atoms for this assembly.
        The second group is formed by the fourth site.
        Sites of the first group (the second and the third) are never present at the same time as the fourth site.
        30 % of times sites 1 and 2 are present (and site 3 is absent); 70 % of times site 3 is present (and sites 1 and 2 are absent).

- **Notes**:
    - Assemblies are essential to represent, for instance, the situation where an atom can statistically occupy two different positions (sites).

    - By defining groups, it is possible to represent, e.g., the case where a functional molecule (and not just one atom) is either present or absent (or the case where it it is present in two conformations)

    - Considerations on virtual alloys and on vacancies: In the special case of a virtual alloy, these specifications allow two different, equivalent ways of specifying them.
        For instance, for a site at the origin with 30 % probability of being occupied by Si, 50 % probability of being occupied by Ge, and 20 % of being a vacancy, the following two representations are possible:

        - Using a single species:
            ```json
            {
              "cartesian_site_positions": [[0,0,0]],
              "species_at_sites": ["SiGe-vac"],
              "species": [
              {
                "name": "SiGe-vac",
                "chemical_symbols": ["Si", "Ge", "vacancy"],
                "concentration": [0.3, 0.5, 0.2]
              }
              ]
              // ...
            }
            ```

        - Using multiple species and the assemblies:
            ```json
            {
              "cartesian_site_positions": [ [0,0,0], [0,0,0], [0,0,0] ],
              "species_at_sites": ["Si", "Ge", "vac"],
              "species": [
                { "name": "Si", "chemical_symbols": ["Si"], "concentration": [1.0] },
                { "name": "Ge", "chemical_symbols": ["Ge"], "concentration": [1.0] },
                { "name": "vac", "chemical_symbols": ["vacancy"], "concentration": [1.0] }
              ],
              "assemblies": [
                {
              "sites_in_groups": [ [0], [1], [2] ],
              "group_probabilities": [0.3, 0.5, 0.2]
                }
              ]
              // ...
            }
            ```

    - It is up to the database provider to decide which representation to use, typically depending on the internal format in which the structure is stored.
        However, given a structure identified by a unique ID, the API implementation MUST always provide the same representation for it.

    - The probabilities of occurrence of different assemblies are uncorrelated.
        So, for instance in the following case with two assemblies:
        ```json
        {
          "assemblies": [
            {
              "sites_in_groups": [ [0], [1] ],
              "group_probabilities": [0.2, 0.8],
            },
            {
              "sites_in_groups": [ [2], [3] ],
              "group_probabilities": [0.3, 0.7]
            }
          ]
        }
        ```

        Site 0 is present with a probability of 20 % and site 1 with a probability of 80 %. These two sites are correlated (either site 0 or 1 is present). Similarly, site 2 is present with a probability of 30 % and site 3 with a probability of 70 %.
        These two sites are correlated (either site 2 or 3 is present).
        However, the presence or absence of sites 0 and 1 is not correlated with the presence or absence of sites 2 and 3 (in the specific example, the pair of sites (0, 2) can occur with 0.2*0.3 = 6 % probability; the pair (0, 3) with 0.2*0.7 = 14 % probability; the pair (1, 2) with 0.8*0.3 = 24 % probability; and the pair (1, 3) with 0.8*0.7 = 56 % probability).""",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.OPTIONAL,
    )

    structure_features: List[StructureFeatures] = OptimadeField(
        ...,
        title="Structure Features",
        description="""A list of strings that flag which special features are used by the structure.

- **Type**: list of strings

- **Requirements/Conventions**:
    - **Support**: MUST be supported by all implementations, MUST NOT be `null`.
    - **Query**: MUST be a queryable property.
    Filters on the list MUST support all mandatory HAS-type queries.
    Filter operators for comparisons on the string components MUST support equality, support for other comparison operators are OPTIONAL.
    - MUST be an empty list if no special features are used.
    - MUST be sorted alphabetically.
    - If a special feature listed below is used, the list MUST contain the corresponding string.
    - If a special feature listed below is not used, the list MUST NOT contain the corresponding string.
    - **List of strings used to indicate special structure features**:
        - `disorder`: this flag MUST be present if any one entry in the `species` list has a `chemical_symbols` list that is longer than 1 element.
        - `implicit_atoms`: this flag MUST be present if the structure contains atoms that are not assigned to sites via the property `species_at_sites` (e.g., because their positions are unknown).
           When this flag is present, the properties related to the chemical formula will likely not match the type and count of atoms represented by the `species_at_sites`, `species` and `assemblies` properties.
        - `site_attachments`: this flag MUST be present if any one entry in the `species` list includes `attached` and `nattached`.
        - `assemblies`: this flag MUST be present if the property `assemblies` is present.

- **Examples**: A structure having implicit atoms and using assemblies: `["assemblies", "implicit_atoms"]`""",
        support=SupportLevel.MUST,
        queryable=SupportLevel.MUST,
    )

    class Config:
        def schema_extra(schema, model):
            """Two things need to be added to the schema:

            1. Constrained types in pydantic do not currently play nicely with
            "Required Optional" fields, i.e. fields must be specified but can be null.
            The two contrained list fields, `dimension_types` and `lattice_vectors`,
            are OPTIMADE 'SHOULD' fields, which means that they are allowed to be null.

            2. All OPTIMADE 'SHOULD' fields are allowed to be null, so we manually set them
            to be `nullable` according to the OpenAPI definition.

            """
            schema["required"].insert(7, "dimension_types")
            schema["required"].insert(9, "lattice_vectors")

            nullable_props = (
                prop
                for prop in schema["required"]
                if schema["properties"][prop].get("support") == SupportLevel.SHOULD
            )
            for prop in nullable_props:
                schema["properties"][prop]["nullable"] = True

    @root_validator(pre=True)
    def warn_on_missing_correlated_fields(cls, values):
        """Emit warnings if a field takes a null value when a value
        was expected based on the value/nullity of another field.
        """
        accumulated_warnings = []
        for field_set in CORRELATED_STRUCTURE_FIELDS:
            missing_fields = {f for f in field_set if values.get(f) is None}
            if missing_fields and len(missing_fields) != len(field_set):
                accumulated_warnings += [
                    f"Structure with values {values} is missing fields {missing_fields} which are required if {field_set - missing_fields} are present."
                ]

        for warn in accumulated_warnings:
            warnings.warn(warn, MissingExpectedField)

        return values

    @validator("chemical_formula_reduced", "chemical_formula_hill")
    def check_ordered_formula(cls, v, field):
        if v is None:
            return v

        numbers = re.findall(r"(\d+\.?)+", v)
        elements = re.findall(r"[A-Z][a-z]?", v)
        expected_elements = sorted(elements)

        if field.name == "chemical_formula_hill":
            # Make sure C is first (and H is second, if present along with C).
            if "C" in expected_elements:
                expected_elements = sorted(
                    expected_elements,
                    key=lambda elem: {"C": "0", "H": "1"}.get(elem, elem),
                )

        if any(elem not in CHEMICAL_SYMBOLS for elem in elements):
            raise ValueError(
                f"Cannot use unknown chemical symbols {[elem for elem in elements if elem not in CHEMICAL_SYMBOLS]} in {field.name!r}"
            )

        if "1" in numbers:
            raise ValueError(
                f"Must omit proportion '1' from formula {v} in {field.name!r}"
            )
        if expected_elements != elements:
            order = "Hill" if field.name == "chemical_formula_hill" else "alphabetical"
            raise ValueError(
                f"Elements in {field.name!r} must appear in {order} order: {expected_elements} not {elements}."
            )

        return v

    @validator("chemical_formula_anonymous")
    def check_anonymous_formula(cls, v):
        if v is None:
            return v

        elements = tuple(re.findall(r"[A-Z][a-z]*", v))
        numbers = [int(n.strip()) for n in re.split(r"[A-Z][a-z]*", v) if n.strip()]

        if any(n == 1 for n in numbers):
            raise ValueError(
                f"'chemical_formula_anonymous' {v} must omit proportion '1'"
            )

        expected_labels = ANONYMOUS_ELEMENTS[: len(elements)]
        expected_numbers = sorted(numbers, reverse=True)

        if expected_numbers != numbers:
            raise ValueError(
                f"'chemical_formula_anonymous' {v} has wrong order: elements with highest proportion should appear first: {numbers} vs expected {expected_numbers}"
            )
        if elements != expected_labels:
            raise ValueError(
                f"'chemical_formula_anonymous' {v} has wrong labels: {elements} vs expected {expected_labels}."
            )

        return v

    @validator("elements", each_item=True)
    def element_must_be_chemical_symbol(cls, v):
        if v not in CHEMICAL_SYMBOLS:
            raise ValueError(f"Only chemical symbols are allowed, you passed: {v}")
        return v

    @validator("elements")
    def elements_must_be_alphabetical(cls, v):
        if v is None:
            return v

        if sorted(v) != v:
            raise ValueError(f"elements must be sorted alphabetically, but is: {v}")
        return v

    @validator("elements_ratios")
    def ratios_must_sum_to_one(cls, v):
        if v is None:
            return v

        if abs(sum(v) - 1) > EPS:
            raise ValueError(
                f"elements_ratios MUST sum to 1 within floating point accuracy. It sums to: {sum(v)}"
            )
        return v

    @validator("nperiodic_dimensions")
    def check_periodic_dimensions(cls, v, values):
        if v is None:
            return v

        if values.get("dimension_types") and v != sum(values.get("dimension_types")):
            raise ValueError(
                f"nperiodic_dimensions ({v}) does not match expected value of {sum(values['dimension_types'])} "
                f"from dimension_types ({values['dimension_types']})"
            )

        return v

    @validator("lattice_vectors", always=True)
    def required_if_dimension_types_has_one(cls, v, values):
        if v is None:
            return v

        if values.get("dimension_types"):
            for dim_type, vector in zip(values.get("dimension_types", (None,) * 3), v):
                if None in vector and dim_type == Periodicity.PERIODIC.value:
                    raise ValueError(
                        f"Null entries in lattice vectors are only permitted when the corresponding dimension type is {Periodicity.APERIODIC.value}. "
                        f"Here: dimension_types = {tuple(getattr(_, 'value', None) for _ in values.get('dimension_types', []))}, lattice_vectors = {v}"
                    )

        return v

    @validator("lattice_vectors")
    def null_values_for_whole_vector(cls, v):
        if v is None:
            return v

        for vector in v:
            if None in vector and any((isinstance(_, float) for _ in vector)):
                raise ValueError(
                    f"A lattice vector MUST be either all `null` or all numbers (vector: {vector}, all vectors: {v})"
                )
        return v

    @validator("nsites")
    def validate_nsites(cls, v, values):
        if v is None:
            return v

        if values.get("cartesian_site_positions") and v != len(
            values.get("cartesian_site_positions", [])
        ):
            raise ValueError(
                f"nsites (value: {v}) MUST equal length of cartesian_site_positions "
                f"(value: {len(values.get('cartesian_site_positions', []))})"
            )
        return v

    @validator("species_at_sites")
    def validate_species_at_sites(cls, v, values):
        if v is None:
            return v

        if values.get("nsites") and len(v) != values.get("nsites"):
            raise ValueError(
                f"Number of species_at_sites (value: {len(v)}) MUST equal number of sites "
                f"(value: {values.get('nsites', 'Not specified')})"
            )
        if values.get("species"):
            all_species_names = {
                getattr(_, "name", None) for _ in values.get("species", [{}])
            }
            all_species_names -= {None}
            for value in v:
                if value not in all_species_names:
                    raise ValueError(
                        "species_at_sites MUST be represented by a species' name, "
                        f"but {value} was not found in the list of species names: {all_species_names}"
                    )
        return v

    @validator("species")
    def validate_species(cls, v):
        if v is None:
            return v

        all_species = [_.name for _ in v]
        unique_species = set(all_species)
        if len(all_species) != len(unique_species):
            raise ValueError(
                f"Species MUST be unique based on their 'name'. Found species names: {all_species}"
            )

        return v

    @validator("structure_features", always=True)
    def validate_structure_features(cls, v, values):
        if [StructureFeatures(value) for value in sorted((_.value for _ in v))] != v:
            raise ValueError(
                f"structure_features MUST be sorted alphabetically, given value: {v}"
            )

        # assemblies
        if values.get("assemblies") is not None:
            if StructureFeatures.ASSEMBLIES not in v:
                raise ValueError(
                    f"{StructureFeatures.ASSEMBLIES.value} MUST be present, since the property of the same name is present"
                )
        elif StructureFeatures.ASSEMBLIES in v:
            raise ValueError(
                f"{StructureFeatures.ASSEMBLIES.value} MUST NOT be present, "
                "since the property of the same name is not present"
            )

        if values.get("species"):
            # disorder
            for species in values.get("species", []):
                if len(species.chemical_symbols) > 1:
                    if StructureFeatures.DISORDER not in v:
                        raise ValueError(
                            f"{StructureFeatures.DISORDER.value} MUST be present when any one entry in species "
                            "has a chemical_symbols list greater than one element"
                        )
                    break
            else:
                if StructureFeatures.DISORDER in v:
                    raise ValueError(
                        f"{StructureFeatures.DISORDER.value} MUST NOT be present, since all species' chemical_symbols "
                        "lists are equal to or less than one element"
                    )
            # site_attachments
            for species in values.get("species", []):
                # There is no need to also test "nattached",
                # since a Species validator makes sure either both are present or both are None.
                if getattr(species, "attached", None) is not None:
                    if StructureFeatures.SITE_ATTACHMENTS not in v:
                        raise ValueError(
                            f"{StructureFeatures.SITE_ATTACHMENTS.value} MUST be present when any one entry "
                            "in species includes attached and nattached"
                        )
                    break
            else:
                if StructureFeatures.SITE_ATTACHMENTS in v:
                    raise ValueError(
                        f"{StructureFeatures.SITE_ATTACHMENTS.value} MUST NOT be present, since no species includes "
                        "the attached and nattached fields"
                    )
            # implicit_atoms
            species_names = [_.name for _ in values.get("species", [])]
            for name in species_names:
                if values.get(
                    "species_at_sites"
                ) is not None and name not in values.get("species_at_sites", []):
                    if StructureFeatures.IMPLICIT_ATOMS not in v:
                        raise ValueError(
                            f"{StructureFeatures.IMPLICIT_ATOMS.value} MUST be present when any one entry in species "
                            "is not represented in species_at_sites"
                        )
                    break
            else:
                if StructureFeatures.IMPLICIT_ATOMS in v:
                    raise ValueError(
                        f"{StructureFeatures.IMPLICIT_ATOMS.value} MUST NOT be present, since all species are "
                        "represented in species_at_sites"
                    )

        return v


class StructureResource(EntryResource):
    """Representing a structure."""

    type: str = StrictField(
        "structures",
        const="structures",
        description="""The name of the type of an entry.

- **Type**: string.

- **Requirements/Conventions**:
    - **Support**: MUST be supported by all implementations, MUST NOT be `null`.
    - **Query**: MUST be a queryable property with support for all mandatory filter features.
    - **Response**: REQUIRED in the response.
    - MUST be an existing entry type.
    - The entry of type `<type>` and ID `<id>` MUST be returned in response to a request for `/<type>/<id>` under the versioned base URL.

- **Examples**:
    - `"structures"`""",
        pattern="^structures$",
        support=SupportLevel.MUST,
        queryable=SupportLevel.MUST,
    )

    attributes: StructureResourceAttributes
