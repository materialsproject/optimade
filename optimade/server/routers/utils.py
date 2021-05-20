# pylint: disable=import-outside-toplevel,too-many-locals
import re
import urllib
from datetime import datetime
from typing import Union, List, Dict, Set

from fastapi import HTTPException, Request
from starlette.datastructures import URL as StarletteURL

from optimade import __api_version__
from optimade.models import (
    ResponseMeta,
    EntryResource,
    EntryResponseMany,
    EntryResponseOne,
    ToplevelLinks,
)

from optimade.server.config import CONFIG
from optimade.server.entry_collections import EntryCollection
from optimade.server.exceptions import BadRequest
from optimade.server.query_params import EntryListingQueryParams, SingleEntryQueryParams

# we need to get rid of any release tags (e.g. -rc.2) and any build metadata (e.g. +py36)
# from the api_version before allowing the URL
BASE_URL_PREFIXES = {
    "major": f"/v{__api_version__.split('-')[0].split('+')[0].split('.')[0]}",
    "minor": f"/v{'.'.join(__api_version__.split('-')[0].split('+')[0].split('.')[:2])}",
    "patch": f"/v{'.'.join(__api_version__.split('-')[0].split('+')[0].split('.')[:3])}",
}


def meta_values(
    url: Union[urllib.parse.ParseResult, urllib.parse.SplitResult, StarletteURL, str],
    data_returned: int,
    data_available: int,
    more_data_available: bool,
    **kwargs,
) -> ResponseMeta:
    """Helper to initialize the meta values"""
    from optimade.models import ResponseMetaQuery

    if isinstance(url, str):
        url = urllib.parse.urlparse(url)

    # To catch all (valid) variations of the version part of the URL, a regex is used
    if re.match(r"/v[0-9]+(\.[0-9]+){,2}/.*", url.path) is not None:
        url_path = re.sub(r"/v[0-9]+(\.[0-9]+){,2}/", "/", url.path)
    else:
        url_path = url.path

    return ResponseMeta(
        query=ResponseMetaQuery(representation=f"{url_path}?{url.query}"),
        api_version=__api_version__,
        time_stamp=datetime.now(),
        data_returned=data_returned,
        more_data_available=more_data_available,
        provider=CONFIG.provider,
        data_available=data_available,
        implementation=CONFIG.implementation,
        **kwargs,
    )


def handle_response_fields(
    results: Union[List[EntryResource], EntryResource],
    exclude_fields: Set[str],
    include_fields: Set[str],
) -> List[dict]:
    """Handle query parameter `response_fields`.

    It is assumed that all fields are under `attributes`.
    This is due to all other top-level fields are REQUIRED in the response.

    Parameters:
        exclude_fields: Fields under `attributes` to be excluded from the response.
        include_fields: Fields under `attributes` that were requested that should be
        set to null if missing in the entry.

    Returns:
        List of resulting resources after pruning according to the `response_fields`
        OPTIMADE URL query parameter.
    """
    if not isinstance(results, list):
        results = [results]

    new_results = []
    while results:
        new_entry = results.pop(0).dict(exclude_unset=True)

        # Remove fields excluded by their omission in `response_fields`
        for field in exclude_fields:
            if field in new_entry["attributes"]:
                del new_entry["attributes"][field]

        # Include missing fields that were requested in `response_fields`
        for field in include_fields:
            if field not in new_entry["attributes"]:
                new_entry["attributes"][field] = None

        new_results.append(new_entry)

    return new_results


def get_included_relationships(
    results: Union[EntryResource, List[EntryResource]],
    ENTRY_COLLECTIONS: Dict[str, EntryCollection],
    include_param: List[str],
) -> Dict[str, List[EntryResource]]:
    """Filters the included relationships and makes the appropriate compound request
    to include them in the response.

    Parameters:
        results: list of returned documents.
        ENTRY_COLLECTIONS: dictionary containing collections to query, with key
            based on endpoint type.
        include_param: list of queried related resources that should be included in
            `included`.

    Returns:
        Dictionary with the same keys as ENTRY_COLLECTIONS, each containing the list
            of resource objects for that entry type.

    """
    from collections import defaultdict

    if not isinstance(results, list):
        results = [results]

    for entry_type in include_param:
        if entry_type not in ENTRY_COLLECTIONS and entry_type != "":
            raise BadRequest(
                detail=f"'{entry_type}' cannot be identified as a valid relationship type. "
                f"Known relationship types: {sorted(ENTRY_COLLECTIONS.keys())}"
            )

    endpoint_includes = defaultdict(dict)
    for doc in results:
        # convert list of references into dict by ID to only included unique IDs
        if doc is None:
            continue

        relationships = doc.relationships
        if relationships is None:
            continue

        relationships = relationships.dict()
        for entry_type in ENTRY_COLLECTIONS:
            # Skip entry type if it is not in `include_param`
            if entry_type not in include_param:
                continue

            entry_relationship = relationships.get(entry_type, {})
            if entry_relationship is not None:
                refs = entry_relationship.get("data", [])
                for ref in refs:
                    if ref["id"] not in endpoint_includes[entry_type]:
                        endpoint_includes[entry_type][ref["id"]] = ref

    included = {}
    for entry_type in endpoint_includes:
        compound_filter = " OR ".join(
            ['id="{}"'.format(ref_id) for ref_id in endpoint_includes[entry_type]]
        )
        params = EntryListingQueryParams(
            filter=compound_filter,
            response_format="json",
            response_fields=None,
            sort=None,
            page_limit=0,
            page_offset=0,
        )

        # still need to handle pagination
        ref_results, _, _, _, _ = ENTRY_COLLECTIONS[entry_type].find(params)
        included[entry_type] = ref_results

    # flatten dict by endpoint to list
    return [obj for endp in included.values() for obj in endp]


def get_base_url(
    parsed_url_request: Union[
        urllib.parse.ParseResult, urllib.parse.SplitResult, StarletteURL, str
    ]
) -> str:
    """Get base URL for current server

    Take the base URL from the config file, if it exists, otherwise use the request.
    """
    parsed_url_request = (
        urllib.parse.urlparse(parsed_url_request)
        if isinstance(parsed_url_request, str)
        else parsed_url_request
    )
    return (
        CONFIG.base_url.rstrip("/")
        if CONFIG.base_url
        else f"{parsed_url_request.scheme}://{parsed_url_request.netloc}"
    )


def get_entries(
    collection: EntryCollection,
    response: EntryResponseMany,
    request: Request,
    params: EntryListingQueryParams,
) -> EntryResponseMany:
    """Generalized /{entry} endpoint getter"""
    from optimade.server.routers import ENTRY_COLLECTIONS

    (
        results,
        data_returned,
        more_data_available,
        fields,
        include_fields,
    ) = collection.find(params)

    include = []
    if getattr(params, "include", False):
        include.extend(params.include.split(","))
    included = get_included_relationships(results, ENTRY_COLLECTIONS, include)

    if more_data_available:
        # Deduce the `next` link from the current request
        query = urllib.parse.parse_qs(request.url.query)
        query["page_offset"] = int(query.get("page_offset", [0])[0]) + len(results)
        urlencoded = urllib.parse.urlencode(query, doseq=True)
        base_url = get_base_url(request.url)

        links = ToplevelLinks(next=f"{base_url}{request.url.path}?{urlencoded}")
    else:
        links = ToplevelLinks(next=None)

    if fields or include_fields:
        results = handle_response_fields(results, fields, include_fields)

    return response(
        links=links,
        data=results,
        meta=meta_values(
            url=request.url,
            data_returned=data_returned,
            data_available=len(collection),
            more_data_available=more_data_available,
        ),
        included=included,
    )


def get_single_entry(
    collection: EntryCollection,
    entry_id: str,
    response: EntryResponseOne,
    request: Request,
    params: SingleEntryQueryParams,
) -> EntryResponseOne:
    from optimade.server.routers import ENTRY_COLLECTIONS

    params.filter = f'id="{entry_id}"'
    (
        results,
        data_returned,
        more_data_available,
        fields,
        include_fields,
    ) = collection.find(params)

    include = []
    if getattr(params, "include", False):
        include.extend(params.include.split(","))
    included = get_included_relationships(results, ENTRY_COLLECTIONS, include)

    if more_data_available:
        raise HTTPException(
            status_code=500,
            detail=f"more_data_available MUST be False for single entry response, however it is {more_data_available}",
        )

    links = ToplevelLinks(next=None)

    if fields or include_fields and results is not None:
        results = handle_response_fields(results, fields, include_fields)[0]

    return response(
        links=links,
        data=results,
        meta=meta_values(
            url=request.url,
            data_returned=data_returned,
            data_available=len(collection),
            more_data_available=more_data_available,
        ),
        included=included,
    )


def mongo_id_for_database(database_id: str, database_type: str) -> str:
    """Produce a MondoDB ObjectId for a database"""
    from bson.objectid import ObjectId

    oid = f"{database_id}{database_type}"
    if len(oid) > 12:
        oid = oid[:12]
    elif len(oid) < 12:
        oid = f"{oid}{'0' * (12 - len(oid))}"

    return str(ObjectId(oid.encode("UTF-8")))


def get_providers() -> list:
    """Retrieve Materials-Consortia providers (from https://providers.optimade.org/v1/links).

    Fallback order if providers.optimade.org is not available:

    1. Try Materials-Consortia/providers on GitHub.
    2. Try submodule `providers`' list of providers.
    3. Log warning that providers list from Materials-Consortia is not included in the
       `/links`-endpoint.

    Returns:
        List of raw JSON-decoded providers including MongoDB object IDs.

    """
    import requests

    try:
        import simplejson as json
    except ImportError:
        import json

    provider_list_urls = [
        "https://providers.optimade.org/v1/links",
        "https://raw.githubusercontent.com/Materials-Consortia/providers"
        "/master/src/links/v1/providers.json",
    ]

    for provider_list_url in provider_list_urls:
        try:
            providers = requests.get(provider_list_url).json()
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.ConnectTimeout,
            json.JSONDecodeError,
        ):
            pass
        else:
            break
    else:
        try:
            from optimade.server.data import providers
        except ImportError:
            from optimade.server.logger import LOGGER

            LOGGER.warning(
                """Could not retrieve a list of providers!

    Tried the following resources:

{}
    The list of providers will not be included in the `/links`-endpoint.
""".format(
                    "".join([f"    * {_}\n" for _ in provider_list_urls])
                )
            )
            return []

    providers_list = []
    for provider in providers.get("data", []):
        # Remove/skip "exmpl"
        if provider["id"] == "exmpl":
            continue

        provider.update(provider.pop("attributes", {}))

        # Add MongoDB ObjectId
        provider["_id"] = {
            "$oid": mongo_id_for_database(provider["id"], provider["type"])
        }

        providers_list.append(provider)

    return providers_list
