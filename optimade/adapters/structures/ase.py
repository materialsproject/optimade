"""
Convert an OPTIMADE structure, in the format of
[`StructureResource`][optimade.models.structures.StructureResource]
to an ASE `Atoms` object.

This conversion function relies on the ASE code.

For more information on the ASE code see [their documentation](https://wiki.fysik.dtu.dk/ase/).
"""
from typing import Dict

from optimade.models import Species as OptimadeStructureSpecies
from optimade.models import StructureResource as OptimadeStructure
from optimade.models import StructureFeatures

from optimade.adapters.exceptions import ConversionError

try:
    from ase import Atoms, Atom
except (ImportError, ModuleNotFoundError):
    from warnings import warn
    from optimade.adapters.warnings import AdapterPackageNotFound

    Atoms = type("Atoms", (), {})
    ASE_NOT_FOUND = "ASE not found, cannot convert structure to an ASE Atoms"


__all__ = ("get_ase_atoms",)


def get_ase_atoms(optimade_structure: OptimadeStructure) -> Atoms:
    """Get ASE `Atoms` from OPTIMADE structure.

    Caution:
        Cannot handle partial occupancies (this includes vacancies).

    Parameters:
        optimade_structure: OPTIMADE structure.

    Returns:
        ASE `Atoms` object.

    """
    if "optimade.adapters" in repr(globals().get("Atoms")):
        warn(ASE_NOT_FOUND, AdapterPackageNotFound)
        return None

    attributes = optimade_structure.attributes

    # Cannot handle partial occupancies
    if StructureFeatures.DISORDER in attributes.structure_features:
        raise ConversionError(
            "ASE cannot handle structures with partial occupancies, sorry."
        )

    species: Dict[str, OptimadeStructureSpecies] = {
        species.name: species for species in attributes.species
    }

    # Since we've made sure there are no species with more than 1 chemical symbol,
    # asking for index 0 will always work.
    if "X" in [specie.chemical_symbols[0] for specie in species.values()]:
        raise ConversionError(
            "ASE cannot handle structures with unknown ('X') chemical symbols, sorry."
        )

    atoms = []
    for site_number in range(attributes.nsites):
        species_name = attributes.species_at_sites[site_number]
        site = attributes.cartesian_site_positions[site_number]

        current_species = species[species_name]

        # Argument above about chemical symbols also holds here
        mass = None
        if current_species.mass:
            mass = current_species.mass[0]

        atoms.append(Atom(symbol=species_name, position=site, mass=mass))

    return Atoms(
        symbols=atoms, cell=attributes.lattice_vectors, pbc=attributes.dimension_types
    )
