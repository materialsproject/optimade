from fastapi import APIRouter, Depends, Request

from optimade.models import (
    StructureResource,
    StructureResponseMany,
    StructureResponseOne,
)
from optimade.server.config import CONFIG
from optimade.server.entry_collections import create_collection
from optimade.server.mappers import StructureMapper
from optimade.server.query_params import EntryListingQueryParams, SingleEntryQueryParams
from optimade.server.routers.utils import get_entries, get_single_entry
from optimade.server.schemas import ERROR_RESPONSES

router = APIRouter(redirect_slashes=True)

structures_coll = create_collection(
    name=CONFIG.structures_collection,
    resource_cls=StructureResource,
    resource_mapper=StructureMapper,
)


@router.get(
    "/structures",
    response_model=StructureResponseMany,
    response_model_exclude_unset=True,
    tags=["Structures"],
    responses=ERROR_RESPONSES,
)
def get_structures(
    request: Request, params: EntryListingQueryParams = Depends()
) -> StructureResponseMany:
    return get_entries(
        collection=structures_coll,
        response=StructureResponseMany,
        request=request,
        params=params,
    )


@router.get(
    "/structures/{entry_id:path}",
    response_model=StructureResponseOne,
    response_model_exclude_unset=True,
    tags=["Structures"],
    responses=ERROR_RESPONSES,
)
def get_single_structure(
    request: Request, entry_id: str, params: SingleEntryQueryParams = Depends()
) -> StructureResponseOne:
    return get_single_entry(
        collection=structures_coll,
        entry_id=entry_id,
        response=StructureResponseOne,
        request=request,
        params=params,
    )
