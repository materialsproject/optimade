"""Test Structure adapter"""
import pytest

from optimade.adapters import Structure
from optimade.models import StructureResource

try:
    import aiida  # noqa: F401
    import ase  # noqa: F401
    import numpy  # noqa: F401
    import pymatgen  # noqa: F401
    import jarvis  # noqa: F401
except ImportError:
    all_modules_found = False
else:
    all_modules_found = True


def test_instantiate(RAW_STRUCTURES):
    """Try instantiating Structure for all raw test structures"""
    for structure in RAW_STRUCTURES:
        new_Structure = Structure(structure)
        assert isinstance(new_Structure.entry, StructureResource)


def test_setting_entry(caplog, RAW_STRUCTURES):
    """Make sure entry can only be set once"""
    structure = Structure(RAW_STRUCTURES[0])
    structure.entry = RAW_STRUCTURES[1]
    assert "entry can only be set once and is already set." in caplog.text


def test_convert(structure):
    """Test convert() works
    Choose currently known entry type - must be updated if no longer available.
    """
    if not structure._type_converters:
        pytest.fail("_type_converters is seemingly empty. This should not be.")

    chosen_type = "cif"
    if chosen_type not in structure._type_converters:
        pytest.fail(
            f"{chosen_type} not found in _type_converters: {structure._type_converters} - "
            "please update test tests/adapters/structures/test_structures.py:TestStructure."
            "test_convert()"
        )

    converted_structure = structure.convert(chosen_type)
    assert isinstance(converted_structure, (str, None.__class__))
    assert converted_structure == structure._converted[chosen_type]


def test_convert_wrong_format(structure):
    """Test AttributeError is raised if format does not exist"""
    nonexistant_format = 0
    right_wrong_format_found = False
    while not right_wrong_format_found:
        if str(nonexistant_format) not in structure._type_converters:
            nonexistant_format = str(nonexistant_format)
            right_wrong_format_found = True
        else:
            nonexistant_format += 1

    with pytest.raises(
        AttributeError,
        match=f"Non-valid entry type to convert to: {nonexistant_format}",
    ):
        structure.convert(nonexistant_format)


def test_getattr_order(structure):
    """The order of getting an attribute should be:
    1. `as_<entry type format>`
    2. `<entry type attribute>`
    3. `<entry type attributes attributes>`
    4. `raise AttributeError` with custom message
    """
    # If passing attribute starting with `as_`, it should call `self.convert()`
    with pytest.raises(AttributeError, match="Non-valid entry type to convert to: "):
        structure.as_

    # If passing valid StructureResource attribute, it should return said attribute
    # Test also nested attributes with `getattr()`.
    for attribute, attribute_type in (
        ("id", str),
        ("species", list),
        ("attributes.species", list),
    ):
        assert isinstance(getattr(structure, attribute), attribute_type)

    # Otherwise, it should raise AttributeError
    for attribute in ("nonexistant_attribute", "attributes.nonexistant_attribute"):
        with pytest.raises(AttributeError, match=f"Unknown attribute: {attribute}"):
            getattr(structure, attribute)


@pytest.mark.skipif(
    all_modules_found,
    reason="This test checks what happens if a conversion-dependent module cannot be found. "
    "All could be found, i.e., it has no meaning.",
)
def test_no_module_conversion(structure):
    """Make sure a warnings is raised and None is returned for conversions with non-existing modules"""
    import importlib
    from optimade.adapters.warnings import AdapterPackageNotFound

    CONVERSION_MAPPING = {
        "aiida": ["aiida_structuredata"],
        "ase": ["ase"],
        "numpy": ["cif", "pdb", "pdbx_mmcif"],
        "pymatgen": ["pymatgen"],
        "jarvis": ["jarvis"],
    }

    modules_to_test = []
    for module in ("aiida", "ase", "numpy", "pymatgen", "jarvis"):
        try:
            importlib.import_module(module)
        except (ImportError, ModuleNotFoundError):
            modules_to_test.append(module)

    if not modules_to_test:
        pytest.fail("No modules found to test - it seems all modules are installed.")

    for module in modules_to_test:
        for conversion_function in CONVERSION_MAPPING[module]:
            with pytest.warns(
                AdapterPackageNotFound, match="not found, cannot convert structure to"
            ):
                converted_structure = structure.convert(conversion_function)
            assert converted_structure is None


def test_common_converters(raw_structure, RAW_STRUCTURES):
    """Test common converters"""
    structure = Structure(raw_structure)

    assert structure.as_json == StructureResource(**raw_structure).json()
    assert structure.as_dict == StructureResource(**raw_structure).dict()

    # Since calling .dict() and .json() will return also all default-valued properties,
    # the raw structure should at least be a sub-set of the resource's full list of properties.
    for raw_structure in RAW_STRUCTURES:
        raw_structure_property_set = set(raw_structure.keys())
        resource_property_set = set(Structure(raw_structure).as_dict.keys())
        assert raw_structure_property_set.issubset(resource_property_set)
