"""
Convert an OPTIMADE structure, in the format of
[`StructureResource`][optimade.models.structures.StructureResource]
to a JARVIS `Atoms` object.

For more information on the NIST-JARVIS repository, see [their website](https://jarvis.nist.gov/).

This conversion function relies on the [jarvis-tools](https://github.com/usnistgov/jarvis) package.

!!! success "Contributing author"
    This conversion function was contributed by Kamal Choudhary ([@knc6](https://github.com/knc6)).
"""
from optimade.models import StructureResource as OptimadeStructure
from optimade.models import StructureFeatures
from optimade.adapters.exceptions import ConversionError

try:
    from jarvis.core.atoms import Atoms
except (ImportError, ModuleNotFoundError):
    from warnings import warn
    from optimade.adapters.warnings import AdapterPackageNotFound

    Atoms = type("Atoms", (), {})
    JARVIS_NOT_FOUND = "jarvis-tools package not found, cannot convert structure to a JARVIS Atoms. Visit https://github.com/usnistgov/jarvis"


__all__ = ("get_jarvis_atoms",)


def get_jarvis_atoms(optimade_structure: OptimadeStructure) -> Atoms:
    """Get jarvis `Atoms` from OPTIMADE structure.

    Caution:
        Cannot handle partial occupancies.

    Parameters:
        optimade_structure: OPTIMADE structure.

    Returns:
        A jarvis `Atoms` object.

    """
    if "optimade.adapters" in repr(globals().get("Atoms")):
        warn(JARVIS_NOT_FOUND, AdapterPackageNotFound)
        return None

    attributes = optimade_structure.attributes

    # Cannot handle partial occupancies
    if StructureFeatures.DISORDER in attributes.structure_features:
        raise ConversionError(
            "jarvis-tools cannot handle structures with partial occupancies."
        )

    return Atoms(
        lattice_mat=attributes.lattice_vectors,
        elements=[specie.name for specie in attributes.species],
        coords=attributes.cartesian_site_positions,
        cartesian=True,
    )
