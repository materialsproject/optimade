import pytest


@pytest.fixture
def structures():
    """Fixture to provide a sorted list of structures."""
    from optimade.server.data import structures

    return sorted(structures, key=lambda x: x["task_id"])


@pytest.fixture
def check_include_response(get_good_response):
    """Fixture to check "good" `include` response"""
    from typing import Union, List, Set

    def inner(
        request: str,
        expected_included_types: Union[List, Set],
        expected_included_resources: Union[List, Set],
        expected_relationship_types: Union[List, Set] = None,
        server: str = "regular",
    ):
        response = get_good_response(request, server)

        response_data = (
            response["data"]
            if isinstance(response["data"], list)
            else [response["data"]]
        )

        included_resource_types = list({_["type"] for _ in response["included"]})
        assert sorted(expected_included_types) == sorted(included_resource_types), (
            f"Expected relationship types: {expected_included_types}. "
            f"Does not match relationship types in response's included field: {included_resource_types}",
        )

        if expected_relationship_types is None:
            expected_relationship_types = expected_included_types
        relationship_types = set()
        for entry in response_data:
            relationship_types.update(set(entry.get("relationships", {}).keys()))
        assert sorted(expected_relationship_types) == sorted(relationship_types), (
            f"Expected relationship types: {expected_relationship_types}. "
            f"Does not match relationship types found in response data: {relationship_types}",
        )

        included_resources = [_["id"] for _ in response["included"]]
        assert len(included_resources) == len(expected_included_resources), response[
            "included"
        ]
        assert sorted(set(included_resources)) == sorted(expected_included_resources)

    return inner


@pytest.fixture
def check_required_fields_response(get_good_response):
    """Fixture to check "good" `required_fields` response"""
    from optimade.server import mappers

    get_mapper = {
        "links": mappers.LinksMapper,
        "references": mappers.ReferenceMapper,
        "structures": mappers.StructureMapper,
    }

    def inner(
        endpoint: str,
        known_unused_fields: set,
        expected_fields: set,
        server: str = "regular",
    ):
        expected_fields |= (
            get_mapper[endpoint].get_required_fields() - known_unused_fields
        )
        expected_fields.add("attributes")
        request = f"/{endpoint}?response_fields={','.join(expected_fields)}"

        response = get_good_response(request, server)

        response_fields = set()
        for entry in response["data"]:
            response_fields.update(set(entry.keys()))
            response_fields.update(set(entry["attributes"].keys()))
        assert sorted(expected_fields) == sorted(response_fields)

    return inner
