from typing import Union

from fastapi import APIRouter, Depends, Request

from optimade.models import ErrorResponse, LinksResponse, LinksResource
from optimade.server.config import CONFIG
from optimade.server.entry_collections import create_collection
from optimade.server.mappers import LinksMapper
from optimade.server.query_params import EntryListingQueryParams

from optimade.server.routers.utils import get_entries

router = APIRouter(redirect_slashes=True)

links_coll = create_collection(
    name=CONFIG.links_collection,
    resource_cls=LinksResource,
    resource_mapper=LinksMapper,
)


@router.get(
    "/links",
    response_model=Union[LinksResponse, ErrorResponse],
    response_model_exclude_unset=True,
    tags=["Links"],
)
def get_links(request: Request, params: EntryListingQueryParams = Depends()):
    return get_entries(
        collection=links_coll, response=LinksResponse, request=request, params=params
    )
