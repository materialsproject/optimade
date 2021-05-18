"""
Convert an OPTIMADE structure, in the format of
[`StructureResource`][optimade.models.structures.StructureResource]
to a PDB file or PDBx/mmCIF file (Protein Data Bank).

For more information on the file formats, see
[this FAQ page](http://www.wwpdb.org/documentation/file-formats-and-the-pdb)
from the [wwPDB](http://www.wwpdb.org) website.

Note:
    These conversion functions are inspired heavily by the similar conversion
    functions in the ASE library.

    See [here (PDB)](https://wiki.fysik.dtu.dk/ase/_modules/ase/io/proteindatabank.html#write_proteindatabank)
    and [here (PDBx/mmCIF)](https://wiki.fysik.dtu.dk/ase/_modules/ase/io/cif.html#write_cif) for the original ASE code.

    For more information on the ASE library, see [their documentation](https://wiki.fysik.dtu.dk/ase/).

These conversion functions both rely on the [NumPy](https://numpy.org/) library.

Warning:
    Currently, the PDBx/mmCIF conversion function is not parsing as a complete PDBx/mmCIF file.
"""
from typing import Dict

try:
    import numpy as np
except ImportError:
    from warnings import warn
    from optimade.adapters.warnings import AdapterPackageNotFound

    np = None
    NUMPY_NOT_FOUND = "NumPy not found, cannot convert structure to your desired format"

from optimade.models import Species as OptimadeStructureSpecies
from optimade.models import StructureResource as OptimadeStructure

from optimade.adapters.structures.utils import (
    cell_to_cellpar,
    cellpar_to_cell,
    fractional_coordinates,
    scaled_cell,
)


__all__ = ("get_pdb", "get_pdbx_mmcif")


def get_pdbx_mmcif(  # pylint: disable=too-many-locals
    optimade_structure: OptimadeStructure,
) -> str:
    """Write Protein Data Bank (PDB) structure in the PDBx/mmCIF format from OPTIMADE structure.

    Warning:
        The result of this function can currently not be parsed as a complete PDBx/mmCIF file.

    Parameters:
        optimade_structure: OPTIMADE structure.

    Return:
        A modern PDBx/mmCIF file as a single Python `str` object.

    """
    if globals().get("np", None) is None:
        warn(NUMPY_NOT_FOUND, AdapterPackageNotFound)
        return None

    cif = """#
# Created from an OPTIMADE structure.
#
# See https://www.optimade.org and/or
# https://github.com/Materials-Consortia/OPTIMADE for more information.
#
# CIF 2.0 format, specifically mmCIF (PDBx).
# See http://mmcif.wwpdb.org for more information.
#
"""

    entry_id = f"{optimade_structure.type}{optimade_structure.id}"
    cif += f"data_{entry_id}\n_entry.id                         {entry_id}\n#\n"

    attributes = optimade_structure.attributes

    # Do this only if there's three non-zero lattice vectors
    if all(attributes.dimension_types):
        a_vector, b_vector, c_vector, alpha, beta, gamma = cell_to_cellpar(
            attributes.lattice_vectors
        )

        cif += (
            f"_cell.entry_id                    {entry_id}\n"
            f"_cell.length_a                    {a_vector:g}\n"
            f"_cell.length_b                    {b_vector:g}\n"
            f"_cell.length_c                    {c_vector:g}\n"
            f"_cell.angle_alpha                 {alpha:g}\n"
            f"_cell.angle_beta                  {beta:g}\n"
            f"_cell.angle_gamma                 {gamma:g}\n"
            "_cell.Z_PDB                       1\n#\n"
        )
        cif += (
            f"_symmetry.entry_id                {entry_id}\n"
            "_symmetry.space_group_name_H-M    'P 1'\n"
            "_symmetry.Int_Tables_number       1\n#\n"
        )

        # Since some structure viewers are having issues with cartesian coordinates,
        # we calculate the fractional coordinates if this is a 3D structure and we have all the necessary information.
        if not hasattr(attributes, "fractional_site_positions"):
            attributes.fractional_site_positions = fractional_coordinates(
                cell=attributes.lattice_vectors,
                cartesian_positions=attributes.cartesian_site_positions,
            )

    # NOTE: The following lines are perhaps needed to create a "valid" PDBx/mmCIF file.
    # However, at the same time, the information here is "default" and will for all structures "at this moment in time"
    # be the same. I.e., no information is gained by adding this now.
    # If it is found that they indeed are needed to create a "valid" PDBx/mmCIF file, they should be included in the output.
    # cif += (
    #     "loop_\n"
    #     "_struct_asym.id\n"
    #     "_struct_asym.entity_id\n"
    #     "A  1\n#\n"  # At this point, not using this feature.
    # )

    # cif += (
    #     "loop_\n"
    #     "_chem_comp.id\n"
    #     "X\n#\n"  # At this point, not using this feature.
    # )

    # cif += (
    #     "loop_\n"
    #     "_entity.id\n"
    #     "1\n#\n"  # At this point, not using this feature.
    # )

    # NOTE: This is otherwise a bit ahead of its time, since this OPTIMADE property is part of an open PR.
    # See https://github.com/Materials-Consortia/OPTIMADE/pull/206
    coord_type = (
        "fract" if hasattr(attributes, "fractional_site_positions") else "Cartn"
    )

    cif += (
        "loop_\n"
        "_atom_site.group_PDB\n"  # Always "ATOM"
        "_atom_site.id\n"  # number (1-counting)
        "_atom_site.type_symbol\n"  # species.chemical_symbols
        "_atom_site.label_atom_id\n"  # species.checmical_symbols symbol + number
        # For these next keys, see the comment above.
        # "_atom_site.label_asym_id\n"  # Will be set to "A" _struct_asym.id above
        # "_atom_site.label_comp_id\n"  # Will be set to "X" _chem_comp.id above
        # "_atom_site.label_entity_id\n"  # Will be set to "1" _entity.id above
        # "_atom_site.label_seq_id\n"
        "_atom_site.occupancy\n"  # species.concentration
        f"_atom_site.{coord_type}_x\n"  # cartesian_site_positions
        f"_atom_site.{coord_type}_y\n"  # cartesian_site_positions
        f"_atom_site.{coord_type}_z\n"  # cartesian_site_positions
        "_atom_site.thermal_displace_type\n"  # Set to 'Biso'
        "_atom_site.B_iso_or_equiv\n"  # Set to 1.0:f
    )

    if coord_type == "fract":
        sites = attributes.fractional_site_positions
    else:
        sites = attributes.cartesian_site_positions

    species: Dict[str, OptimadeStructureSpecies] = {
        species.name: species for species in attributes.species
    }

    for site_number in range(attributes.nsites):
        species_name = attributes.species_at_sites[site_number]
        site = sites[site_number]

        current_species = species[species_name]

        for index, symbol in enumerate(current_species.chemical_symbols):
            if symbol == "vacancy":
                continue

            label = f"{species_name.upper()}{site_number + 1}"
            if len(current_species.chemical_symbols) > 1:
                if (
                    "vacancy" in current_species.chemical_symbols
                    and len(current_species.chemical_symbols) == 2
                ):
                    pass
                else:
                    label = f"{symbol.upper()}{index + 1}"

            cif += (
                f"ATOM  {site_number + 1:5d}  {symbol}  {label:8}  "
                f"{current_species.concentration[index]:6.4f}  {site[0]:8.5f}  "
                f"{site[1]:8.5f}  {site[2]:8.5f}  {'Biso':4}  {'1.000':6}\n"
            )

    return cif


def get_pdb(  # pylint: disable=too-many-locals
    optimade_structure: OptimadeStructure,
) -> str:
    """Write Protein Data Bank (PDB) structure in the old PDB format from OPTIMADE structure.

    Parameters:
        optimade_structure: OPTIMADE structure.

    Returns:
        A PDB file as a single Python `str` object.

    """
    if globals().get("np", None) is None:
        warn(NUMPY_NOT_FOUND, AdapterPackageNotFound)
        return None

    pdb = ""

    attributes = optimade_structure.attributes

    rotation = None
    if all(attributes.dimension_types):
        currentcell = np.asarray(attributes.lattice_vectors)
        cellpar = cell_to_cellpar(currentcell)
        exportedcell = cellpar_to_cell(cellpar)
        rotation = np.linalg.solve(currentcell, exportedcell)
        # Setting Z-value = 1 and using P1 since we have all atoms defined explicitly
        Z = 1
        spacegroup = "P 1"
        pdb += (
            f"CRYST1{cellpar[0]:9.3f}{cellpar[1]:9.3f}{cellpar[2]:8.3f}"
            f"{cellpar[3]:7.2f}{cellpar[4]:7.2f}{cellpar[5]:7.2f} {spacegroup:11s}{Z:4d}\n"
        )

        for i, vector in enumerate(scaled_cell(currentcell)):
            pdb += f"SCALE{i + 1}    {vector[0]:10.6f}{vector[1]:10.6f}{vector[2]:10.6f}     {0:10.5f}\n"

    # There is a limit of 5 digit numbers in this field.
    pdb_maxnum = 100000
    bfactor = 1.0

    pdb += "MODEL     1\n"

    species: Dict[str, OptimadeStructureSpecies] = {
        species.name: species for species in attributes.species
    }

    sites = np.asarray(attributes.cartesian_site_positions)
    if rotation is not None:
        sites = sites.dot(rotation)

    for site_number in range(attributes.nsites):
        species_name = attributes.species_at_sites[site_number]
        site = sites[site_number]

        current_species = species[species_name]

        for index, symbol in enumerate(current_species.chemical_symbols):
            if symbol == "vacancy":
                continue

            label = species_name
            if len(current_species.chemical_symbols) > 1:
                if (
                    "vacancy" in current_species.chemical_symbols
                    and len(current_species.chemical_symbols) == 2
                ):
                    pass
                else:
                    label = f"{symbol}{index + 1}"

            pdb += (
                f"ATOM  {site_number % pdb_maxnum:5d} {label:4} MOL     1    "
                f"{site[0]:8.3f}{site[1]:8.3f}{site[2]:8.3f}"
                f"{current_species.concentration[index]:6.2f}"
                f"{bfactor:6.2f}          {symbol.upper():2}  \n"
            )
    pdb += "ENDMDL\n"

    return pdb
