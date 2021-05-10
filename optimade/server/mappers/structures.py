from optimade.server.mappers.entries import BaseResourceMapper
from optimade.models.structures import StructureResource

__all__ = ("StructureMapper",)


class StructureMapper(BaseResourceMapper):

    LENGTH_ALIASES = (
        ("elements", "nelements"),
        ("element_ratios", "nelements"),
        ("cartesian_site_positions", "nsites"),
        ("species_at_sites", "nsites"),
    )
    ENTRY_RESOURCE_CLASS = StructureResource
