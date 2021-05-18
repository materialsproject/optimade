from optimade.server.mappers.entries import BaseResourceMapper
from optimade.models.links import LinksResource

__all__ = ("LinksMapper",)


class LinksMapper(BaseResourceMapper):

    ENDPOINT = "links"

    ENTRY_RESOURCE_CLASS = LinksResource

    @classmethod
    def map_back(cls, doc: dict) -> dict:
        """Map properties from MongoDB to OPTIMADE

        :param doc: A resource object in MongoDB format
        :type doc: dict

        :return: A resource object in OPTIMADE format
        :rtype: dict
        """
        type_ = doc["type"]
        newdoc = super().map_back(doc)
        newdoc["type"] = type_
        return newdoc
