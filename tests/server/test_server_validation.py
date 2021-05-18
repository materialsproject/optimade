import json
import dataclasses

import pytest

from optimade.validator import ImplementationValidator


def test_with_validator(both_fake_remote_clients):
    from optimade.server.main_index import app

    validator = ImplementationValidator(
        client=both_fake_remote_clients,
        index=both_fake_remote_clients.app == app,
    )

    validator.validate_implementation()
    assert validator.valid


def test_with_validator_json_response(both_fake_remote_clients, capsys):
    """Test that the validator writes compliant JSON when requested."""
    from optimade.server.main_index import app

    validator = ImplementationValidator(
        client=both_fake_remote_clients,
        index=both_fake_remote_clients.app == app,
        respond_json=True,
    )
    validator.validate_implementation()

    captured = capsys.readouterr()
    json_response = json.loads(captured.out)
    assert json_response["failure_count"] == 0, json_response
    assert json_response["internal_failure_count"] == 0, json_response
    assert json_response["optional_failure_count"] == 0, json_response
    assert validator.results.failure_count == 0, json_response
    assert validator.results.internal_failure_count == 0, json_response
    assert validator.results.optional_failure_count == 0, json_response
    assert dataclasses.asdict(validator.results) == json_response, json_response
    assert validator.valid


def test_as_type_with_validator(client, capsys):
    from unittest.mock import patch, Mock

    test_urls = {
        f"{client.base_url}/structures": "structures",
        f"{client.base_url}/structures/mpf_1": "structure",
        f"{client.base_url}/references": "references",
        f"{client.base_url}/references/dijkstra1968": "reference",
        f"{client.base_url}/info": "info",
        f"{client.base_url}/links": "links",
    }
    with patch("requests.get", Mock(side_effect=client.get)):
        for url, as_type in test_urls.items():
            validator = ImplementationValidator(
                base_url=url, as_type=as_type, respond_json=True
            )
            validator.validate_implementation()
            assert validator.valid

            captured = capsys.readouterr()
            json_response = json.loads(captured.out)

            assert json_response["failure_count"] == 0
            assert json_response["internal_failure_count"] == 0
            assert json_response["optional_failure_count"] == 0
            assert validator.results.failure_count == 0
            assert validator.results.internal_failure_count == 0
            assert validator.results.optional_failure_count == 0
            assert dataclasses.asdict(validator.results) == json_response


def test_query_value_formatting(client):
    from optimade.models.optimade_json import DataType

    format_value_fn = ImplementationValidator._format_test_value

    assert format_value_fn(["Ag", "Ba", "Ca"], DataType.LIST, "HAS") == '"Ag"'
    assert (
        format_value_fn(["Ag", "Ba", "Ca"], DataType.LIST, "HAS ANY")
        == '"Ag","Ba","Ca"'
    )
    assert format_value_fn([6, 1, 4], DataType.LIST, "HAS ALL") == "1,4,6"
    assert format_value_fn("test value", DataType.STRING, "CONTAINS") == '"test value"'
    assert format_value_fn(5, DataType.INTEGER, "=") == 5


@pytest.mark.parametrize("server", ["regular", "index"])
def test_versioned_base_urls(client, index_client, server: str):
    """Test all expected versioned base URLs responds with 200

    This depends on the routers for each kind of server.
    """
    try:
        import simplejson as json
    except ImportError:
        import json

    from optimade.server.routers.utils import BASE_URL_PREFIXES

    clients = {
        "regular": client,
        "index": index_client,
    }

    valid_endpoints = {
        "regular": ("/info", "/links", "/references", "/structures"),
        "index": ("/info", "/links"),
    }

    for version in BASE_URL_PREFIXES.values():
        for endpoint in valid_endpoints[server]:
            response = clients[server].get(url=version + endpoint)
            json_response = response.json()

            assert response.status_code == 200, (
                f"Request to {response.url} failed for server {server!r}: "
                f"{json.dumps(json_response, indent=2)}"
            )
            assert "meta" in json_response, (
                f"Mandatory 'meta' top-level field not found in request to {response.url} for "
                f"server {server!r}. Response: {json.dumps(json_response, indent=2)}"
            )
