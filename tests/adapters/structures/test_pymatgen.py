# pylint: disable=import-error
import pytest

from .utils import get_min_ver

min_ver = get_min_ver("pymatgen")
pymatgen = pytest.importorskip(
    "pymatgen",
    minversion=min_ver,
    reason=f"pymatgen must be installed with minimum version {min_ver} for these tests to"
    " be able to run",
)

from pymatgen.core import Molecule, Structure as PymatgenStructure

from optimade.adapters import Structure
from optimade.adapters.structures.pymatgen import (
    get_pymatgen,
    _get_structure,
    _get_molecule,
)


def test_successful_conversion(RAW_STRUCTURES):
    """Make sure its possible to convert"""
    for structure in RAW_STRUCTURES:
        assert isinstance(
            get_pymatgen(Structure(structure)), (PymatgenStructure, Molecule)
        )


def test_successful_conversion_structure(structure):
    """Make sure its possible to convert to pymatgen Structure"""
    assert isinstance(_get_structure(structure), PymatgenStructure)
    assert isinstance(get_pymatgen(structure), PymatgenStructure)


def test_null_lattice_vectors(null_lattice_vector_structure):
    """Make sure null lattice vectors are handled

    This also respresents a test for successful conversion to pymatgen Molecule
    """
    assert isinstance(_get_molecule(null_lattice_vector_structure), Molecule)
    assert isinstance(get_pymatgen(null_lattice_vector_structure), Molecule)


def test_special_species(SPECIAL_SPECIES_STRUCTURES):
    """Make sure vacancies and non-chemical symbols ("X") are handled"""
    for special_structure in SPECIAL_SPECIES_STRUCTURES:
        structure = Structure(special_structure)
        assert isinstance(get_pymatgen(structure), PymatgenStructure)
