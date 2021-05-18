"""
Convert an OPTIMADE structure, in the format of
[`StructureResource`][optimade.models.structures.StructureResource]
to a pymatgen `Molecule` or `Structure` object.

This conversion function relies on the [pymatgen](https://github.com/materialsproject/pymatgen) package.

For more information on the pymatgen code see [their documentation](https://pymatgen.org).
"""
from typing import Union, Dict, List

from optimade.models import Species as OptimadeStructureSpecies
from optimade.models import StructureResource as OptimadeStructure

try:
    from pymatgen.core import Structure, Molecule

except (ImportError, ModuleNotFoundError):
    from warnings import warn
    from optimade.adapters.warnings import AdapterPackageNotFound

    Structure = type("Structure", (), {})
    Molecule = type("Molecule", (), {})
    PYMATGEN_NOT_FOUND = "Pymatgen not found, cannot convert structure to a pymatgen Structure or Molecule"


__all__ = ("get_pymatgen",)


def get_pymatgen(optimade_structure: OptimadeStructure) -> Union[Structure, Molecule]:
    """Get pymatgen `Structure` or `Molecule` from OPTIMADE structure.

    This function will return either a pymatgen `Structure` or `Molecule` based
    on the periodicity or periodic dimensionality of OPTIMADE structure.

    For bulk, three-dimensional structures, a pymatgen `Structure` is returned.
    This means, if the [`dimension_types`][optimade.models.structures.StructureResourceAttributes.dimension_types]
    attribute is comprised of all `1`s (or [`Periodicity.PERIODIC`][optimade.models.structures.Periodicity.PERIODIC]s).

    Otherwise, a pymatgen `Molecule` is returned.

    Parameters:
        optimade_structure: OPTIMADE structure.

    Returns:
        A pymatgen `Structure` or `Molecule` based on the periodicity of the
        OPTIMADE structure.

    """
    if "optimade.adapters" in repr(globals().get("Structure")):
        warn(PYMATGEN_NOT_FOUND, AdapterPackageNotFound)
        return None

    if all(optimade_structure.attributes.dimension_types):
        return _get_structure(optimade_structure)

    return _get_molecule(optimade_structure)


def _get_structure(optimade_structure: OptimadeStructure) -> Structure:
    """Create pymatgen Structure from OPTIMADE structure"""

    attributes = optimade_structure.attributes

    return Structure(
        lattice=attributes.lattice_vectors,
        species=_pymatgen_species(
            nsites=attributes.nsites,
            species=attributes.species,
            species_at_sites=attributes.species_at_sites,
        ),
        coords=attributes.cartesian_site_positions,
        coords_are_cartesian=True,
    )


def _get_molecule(optimade_structure: OptimadeStructure) -> Molecule:
    """Create pymatgen Molecule from OPTIMADE structure"""

    attributes = optimade_structure.attributes

    return Molecule(
        species=_pymatgen_species(
            nsites=attributes.nsites,
            species=attributes.species,
            species_at_sites=attributes.species_at_sites,
        ),
        coords=attributes.cartesian_site_positions,
    )


def _pymatgen_species(
    nsites: int, species: List[OptimadeStructureSpecies], species_at_sites: List[str]
) -> List[Dict[str, float]]:
    """
    Create list of {"symbol": "concentration"} per site for values to pymatgen species parameters.
    Remove vacancies, if they are present.
    """

    optimade_species = {_.name: _ for _ in species}

    pymatgen_species = []
    for site_number in range(nsites):
        species_name = species_at_sites[site_number]
        current_species = optimade_species[species_name]

        chemical_symbols = []
        concentration = []
        for index, symbol in enumerate(current_species.chemical_symbols):
            if symbol == "vacancy":
                # Skip. This is how pymatgen handles vacancies;
                # to not include them, while keeping the concentration in a site less than 1.
                continue
            else:
                chemical_symbols.append(symbol)
                concentration.append(current_species.concentration[index])

        pymatgen_species.append(dict(zip(chemical_symbols, concentration)))

    return pymatgen_species
