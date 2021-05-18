"""
Convert an OPTIMADE structure, in the format of
[`StructureResource`][optimade.models.structures.StructureResource]
to a CIF file (Crystallographic Information File).

For more information on the CIF file format, see
[the official documentation](https://www.iucr.org/resources/cif/documentation).

Note:
    This conversion function is inspired heavily by the similar conversion
    function in the ASE library.

    See [here](https://wiki.fysik.dtu.dk/ase/_modules/ase/io/cif.html#write_cif) for the original ASE code.

    For more information on the ASE library, see [their documentation](https://wiki.fysik.dtu.dk/ase/).

This conversion function relies on the [NumPy](https://numpy.org/) library.
"""
from typing import Dict

from optimade.models import Species as OptimadeStructureSpecies
from optimade.models import StructureResource as OptimadeStructure

from optimade.adapters.structures.utils import (
    cell_to_cellpar,
    fractional_coordinates,
)

try:
    import numpy as np
except ImportError:
    from warnings import warn
    from optimade.adapters.warnings import AdapterPackageNotFound

    np = None
    NUMPY_NOT_FOUND = "NumPy not found, cannot convert structure to CIF"


__all__ = ("get_cif",)


def get_cif(  # pylint: disable=too-many-locals,too-many-branches
    optimade_structure: OptimadeStructure,
) -> str:
    """Get CIF file as string from OPTIMADE structure.

    Parameters:
        optimade_structure: OPTIMADE structure.

    Returns:
        The CIF file as a single Python `str` object.

    """
    # NumPy is needed for calculations
    if globals().get("np", None) is None:
        warn(NUMPY_NOT_FOUND, AdapterPackageNotFound)
        return None

    cif = """#
# Created from an OPTIMADE structure.
#
# See https://www.optimade.org and/or
# https://github.com/Materials-Consortia/OPTIMADE for more information.
#
"""

    cif += f"data_{optimade_structure.id}\n\n"

    attributes = optimade_structure.attributes

    # Do this only if there's three non-zero lattice vectors
    # NOTE: This also negates handling of lattice_vectors with null/None values
    if all(attributes.dimension_types):
        a_vector, b_vector, c_vector, alpha, beta, gamma = cell_to_cellpar(
            attributes.lattice_vectors
        )

        cif += (
            f"_cell_length_a                    {a_vector:g}\n"
            f"_cell_length_b                    {b_vector:g}\n"
            f"_cell_length_c                    {c_vector:g}\n"
            f"_cell_angle_alpha                 {alpha:g}\n"
            f"_cell_angle_beta                  {beta:g}\n"
            f"_cell_angle_gamma                 {gamma:g}\n\n"
        )
        cif += (
            "_symmetry_space_group_name_H-M    'P 1'\n"
            "_symmetry_int_tables_number       1\n\n"
            "loop_\n"
            "  _symmetry_equiv_pos_as_xyz\n"
            "  'x, y, z'\n\n"
        )

        # Since some structure viewers are having issues with cartesian coordinates,
        # we calculate the fractional coordinates if this is a 3D structure and we have all the necessary information.
        if not hasattr(attributes, "fractional_site_positions"):
            attributes.fractional_site_positions = fractional_coordinates(
                cell=attributes.lattice_vectors,
                cartesian_positions=attributes.cartesian_site_positions,
            )

    # NOTE: This is otherwise a bit ahead of its time, since this OPTIMADE property is part of an open PR.
    # See https://github.com/Materials-Consortia/OPTIMADE/pull/206
    coord_type = (
        "fract" if hasattr(attributes, "fractional_site_positions") else "Cartn"
    )

    cif += (
        "loop_\n"
        "  _atom_site_type_symbol\n"  # species.chemical_symbols
        "  _atom_site_label\n"  # species.name + unique int
        "  _atom_site_occupancy\n"  # species.concentration
        f"  _atom_site_{coord_type}_x\n"  # cartesian_site_positions
        f"  _atom_site_{coord_type}_y\n"  # cartesian_site_positions
        f"  _atom_site_{coord_type}_z\n"  # cartesian_site_positions
        "  _atom_site_thermal_displace_type\n"  # Set to 'Biso'
        "  _atom_site_B_iso_or_equiv\n"  # Set to 1.0:f
    )

    if coord_type == "fract":
        sites = attributes.fractional_site_positions
    else:
        sites = attributes.cartesian_site_positions

    species: Dict[str, OptimadeStructureSpecies] = {
        species.name: species for species in attributes.species
    }

    symbol_occurences = {}
    for site_number in range(attributes.nsites):
        species_name = attributes.species_at_sites[site_number]
        site = sites[site_number]

        current_species = species[species_name]

        for index, symbol in enumerate(current_species.chemical_symbols):
            if symbol == "vacancy":
                continue

            if symbol in symbol_occurences:
                symbol_occurences[symbol] += 1
            else:
                symbol_occurences[symbol] = 1
            label = f"{symbol}{symbol_occurences[symbol]}"

            cif += (
                f"  {symbol} {label} {current_species.concentration[index]:6.4f} {site[0]:8.5f}  "
                f"{site[1]:8.5f}  {site[2]:8.5f}  {'Biso':4}  {'1.000':6}\n"
            )

    return cif
