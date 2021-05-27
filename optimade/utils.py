from typing import List

from optimade.models.links import LinksResource


def mongo_id_for_database(database_id: str, database_type: str) -> str:
    """Produce a MongoDB ObjectId for a database"""
    from bson.objectid import ObjectId

    oid = f"{database_id}{database_type}"
    if len(oid) > 12:
        oid = oid[:12]
    elif len(oid) < 12:
        oid = f"{oid}{'0' * (12 - len(oid))}"

    return str(ObjectId(oid.encode("UTF-8")))


def get_providers(add_mongo_id: bool = False) -> list:
    """Retrieve Materials-Consortia providers (from https://providers.optimade.org/v1/links).

    Fallback order if providers.optimade.org is not available:

    1. Try Materials-Consortia/providers on GitHub.
    2. Try submodule `providers`' list of providers.
    3. Log warning that providers list from Materials-Consortia is not included in the
       `/links`-endpoint.

    Arguments:
        Whether to populate the `_id` field of the provider with MongoDB ObjectID.

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
        if add_mongo_id:
            provider["_id"] = {
                "$oid": mongo_id_for_database(provider["id"], provider["type"])
            }

        providers_list.append(provider)

    return providers_list


def get_child_database_links(provider: LinksResource) -> List[LinksResource]:
    """For a provider, return a list of available child databases.

    Arguments:
        provider: The links entry for the provider.

    Returns:
        A list of the valid links entries from this provider that
        have `link_type` `"child"`.

    """
    import requests
    from optimade.models.responses import LinksResponse
    from optimade.models.links import LinkType

    base_url = provider.pop("base_url")
    if base_url is None:
        raise RuntimeError(f"Provider {provider['id']} provides no base URL.")

    links_endp = base_url + "/v1/links"
    links = requests.get(links_endp)

    if links.status_code != 200:
        raise RuntimeError(
            f"Invalid response from {links_endp} for provider {provider['id']}: {links.content}."
        )

    links = LinksResponse(**links.json())
    return [
        link
        for link in links.data
        if link.attributes.link_type == LinkType.child
        and link.attributes.base_url is not None
    ]
