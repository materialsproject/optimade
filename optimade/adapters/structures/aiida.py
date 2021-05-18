"""
Convert an OPTIMADE structure, in the format of
[`StructureResource`][optimade.models.structures.StructureResource]
to an AiiDA `StructureData` Node.

For more information on the AiiDA code see [their website](http://www.aiida.net).

This conversion function relies on the [`aiida-core`](https://github.com/aiidateam/aiida-core) package.
"""
from warnings import warn

from optimade.models import StructureResource as OptimadeStructure

from optimade.adapters.warnings import AdapterPackageNotFound, ConversionWarning
from optimade.adapters.structures.utils import pad_cell

try:
    from aiida.orm.nodes.data.structure import StructureData, Kind, Site
except (ImportError, ModuleNotFoundError):
    StructureData = type("StructureData", (), {})
    AIIDA_NOT_FOUND = (
        "AiiDA not found, cannot convert structure to an AiiDA StructureData"
    )


__all__ = ("get_aiida_structure_data",)


def get_aiida_structure_data(optimade_structure: OptimadeStructure) -> StructureData:
    """Get AiiDA `StructureData` from OPTIMADE structure.

    Parameters:
        optimade_structure: OPTIMADE structure.

    Returns:
        AiiDA `StructureData` Node.

    """
    if "optimade.adapters" in repr(globals().get("StructureData")):
        warn(AIIDA_NOT_FOUND, AdapterPackageNotFound)
        return None

    attributes = optimade_structure.attributes

    # Convert null/None values to float("nan")
    lattice_vectors, adjust_cell = pad_cell(attributes.lattice_vectors)
    structure = StructureData(cell=lattice_vectors)

    # Add Kinds
    for kind in attributes.species:
        symbols = []
        concentration = []
        mass = 0.0
        for index, chemical_symbol in enumerate(kind.chemical_symbols):
            # NOTE: The non-chemical element identifier "X" is identical to how AiiDA handles this,
            # so it will be treated the same as any other true chemical identifier.
            if chemical_symbol == "vacancy":
                # Skip. This is how AiiDA handles vacancies;
                # to not include them, while keeping the concentration in a site less than 1.
                continue
            else:
                symbols.append(chemical_symbol)
                concentration.append(kind.concentration[index])

                # AiiDA needs a definition for the mass, and for it to be > 0
                # mass is OPTIONAL for OPTIMADE structures
                if kind.mass:
                    mass += kind.concentration[index] * kind.mass[index]

        if not mass:
            warn(
                f"No mass defined for <species(name={kind.name!r})>, will default to setting mass to 1.0.",
                ConversionWarning,
            )

        structure.append_kind(
            Kind(
                symbols=symbols, weights=concentration, mass=mass or 1.0, name=kind.name
            )
        )

    # Add Sites
    for index in range(attributes.nsites):
        # range() to ensure 1-to-1 between kind and site
        structure.append_site(
            Site(
                kind_name=attributes.species_at_sites[index],
                position=attributes.cartesian_site_positions[index],
            )
        )

    if adjust_cell:
        structure._adjust_default_cell(
            pbc=[bool(dim.value) for dim in attributes.dimension_types]
        )

    return structure
