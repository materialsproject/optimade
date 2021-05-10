from optimade.server.mappers.entries import BaseResourceMapper
from optimade.models.references import ReferenceResource

__all__ = ("ReferenceMapper",)


class ReferenceMapper(BaseResourceMapper):

    ENTRY_RESOURCE_CLASS = ReferenceResource
