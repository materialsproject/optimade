# pylint: disable=import-error

import pytest

from .utils import get_min_ver

min_ver = get_min_ver("aiida-core")
aiida = pytest.importorskip(
    "aiida",
    minversion=min_ver,
    reason=f"aiida-core must be installed with minimum version {min_ver} for these tests to"
    " be able to run",
)

from aiida import load_profile

load_profile()

from aiida.orm import StructureData

from optimade.adapters import Structure
from optimade.adapters.structures.aiida import get_aiida_structure_data


def test_successful_conversion(RAW_STRUCTURES):
    """Make sure its possible to convert"""
    for structure in RAW_STRUCTURES:
        assert isinstance(get_aiida_structure_data(Structure(structure)), StructureData)


def test_null_lattice_vectors(null_lattice_vector_structure):
    """Make sure null lattice vectors are handled"""
    assert isinstance(
        get_aiida_structure_data(null_lattice_vector_structure), StructureData
    )


def test_special_species(SPECIAL_SPECIES_STRUCTURES):
    """Make sure vacancies and non-chemical symbols ("X") are handled"""
    from optimade.adapters.warnings import ConversionWarning

    for special_structure in SPECIAL_SPECIES_STRUCTURES:
        structure = Structure(special_structure)

        if structure.attributes.species[0].mass:
            aiida_structure = get_aiida_structure_data(structure)
        else:
            with pytest.warns(
                ConversionWarning, match=r".*will default to setting mass to 1\.0\.$"
            ):
                aiida_structure = get_aiida_structure_data(structure)

        assert isinstance(aiida_structure, StructureData)

        # Test species.chemical_symbols
        if "vacancy" in structure.attributes.species[0].chemical_symbols:
            assert aiida_structure.has_vacancies
            assert not aiida_structure.is_alloy
        elif len(structure.attributes.species[0].chemical_symbols) > 1:
            assert not aiida_structure.has_vacancies
            assert aiida_structure.is_alloy
        else:
            assert not aiida_structure.has_vacancies
            assert not aiida_structure.is_alloy

        # Test species.mass
        if structure.attributes.species[0].mass:
            if len(structure.attributes.species[0].mass) > 1:
                assert aiida_structure.kinds[0].mass == sum(
                    [
                        conc * mass
                        for conc, mass in zip(
                            structure.attributes.species[0].concentration,
                            structure.attributes.species[0].mass,
                        )
                    ]
                )
            else:
                assert (
                    aiida_structure.kinds[0].mass
                    == structure.attributes.species[0].mass[0]
                )
        else:
            assert aiida_structure.kinds[0].mass == 1.0
