from typing import Union, Dict

import pytest


@pytest.fixture(scope="session")
def client():
    """Return TestClient for the regular OPTIMADE server"""
    from .utils import client_factory

    return client_factory()(server="regular")


@pytest.fixture(scope="session")
def index_client():
    """Return TestClient for the index OPTIMADE server"""
    from .utils import client_factory

    return client_factory()(server="index")


@pytest.fixture(scope="session", params=["regular", "index"])
def both_clients(request):
    """Return TestClient for both the regular and index OPTIMADE server"""
    from .utils import client_factory

    return client_factory()(server=request.param)


@pytest.fixture(scope="session", params=["regular", "index"])
def both_fake_remote_clients(request):
    """Return TestClient for both the regular and index OPTIMADE server, with
    the additional option `raise_server_exceptions` set to `False`, to mimic a
    remote webserver.

    """
    from .utils import client_factory

    return client_factory()(server=request.param, raise_server_exceptions=False)


@pytest.fixture
def get_good_response(client, index_client):
    """Get response with some sanity checks, expecting '200 OK'"""
    try:
        import simplejson as json
    except ImportError:
        import json

    from requests import Response

    from .utils import OptimadeTestClient

    def inner(
        request: str,
        server: Union[str, OptimadeTestClient] = "regular",
        return_json: bool = True,
        **kwargs,
    ) -> Union[dict, Response]:
        if isinstance(server, str):
            if server == "regular":
                used_client = client
            elif server == "index":
                used_client = index_client
            else:
                pytest.fail(
                    f"Wrong value for 'server': {server}. It must be either 'regular' or 'index'."
                )
        elif isinstance(server, OptimadeTestClient):
            used_client = server
        else:
            pytest.fail("'server' must be either a string or an OptimadeTestClient.")

        try:
            response = used_client.get(request, **kwargs)
            response_json = response.json()
            assert response.status_code == 200, f"Request failed: {response_json}"
        except json.JSONDecodeError:
            print(
                f"Request attempted:\n{used_client.base_url}{used_client.version}"
                f"{request}\n"
                "Could not successfully decode response as JSON."
            )
            raise
        except Exception as exc:
            print(
                f"Request attempted:\n{used_client.base_url}{used_client.version}"
                f"{request}"
            )
            raise exc
        else:
            if return_json:
                return response_json
            return response

    return inner


@pytest.fixture
def check_response(get_good_response):
    """Fixture to check "good" response"""
    from typing import List
    from optimade.server.config import CONFIG
    from .utils import OptimadeTestClient

    def inner(
        request: str,
        expected_ids: List[str],
        page_limit: int = CONFIG.page_limit,
        expected_return: int = None,
        expected_as_is: bool = False,
        expected_warnings: List[Dict[str, str]] = None,
        server: Union[str, OptimadeTestClient] = "regular",
    ):
        response = get_good_response(request, server)

        response_ids = [struct["id"] for struct in response["data"]]

        if expected_return is None:
            expected_return = len(expected_ids)

        assert response["meta"]["data_returned"] == expected_return

        if not expected_as_is:
            expected_ids = sorted(expected_ids)

        if len(expected_ids) > page_limit:
            assert expected_ids[:page_limit] == response_ids
        else:
            assert expected_ids == response_ids

        expected_warnings = expected_warnings if expected_warnings else []
        if expected_warnings:
            assert "warnings" in response["meta"]
            assert len(expected_warnings) == len(response["meta"]["warnings"])
            for ind, warn in enumerate(expected_warnings):
                for key in warn:
                    assert response["meta"]["warnings"][ind][key] == warn[key]
        else:
            assert "warnings" not in response["meta"]

    return inner


@pytest.fixture
def check_error_response(client, index_client):
    """General method for testing expected erroneous response"""
    from .utils import OptimadeTestClient

    def inner(
        request: str,
        expected_status: int = None,
        expected_title: str = None,
        expected_detail: str = None,
        server: Union[str, OptimadeTestClient] = "regular",
    ):
        response = None
        if isinstance(server, str):
            if server == "regular":
                used_client = client
            elif server == "index":
                used_client = index_client
            else:
                pytest.fail(
                    f"Wrong value for 'server': {server}. It must be either 'regular' or 'index'."
                )
        elif isinstance(server, OptimadeTestClient):
            used_client = server
        else:
            pytest.fail("'server' must be either a string or an OptimadeTestClient.")

        try:
            response = used_client.get(request)
            assert response.status_code == expected_status, (
                f"Request should have been an error with status code {expected_status}, "
                f"but instead {response.status_code} was received.\nResponse:\n{response.json()}",
            )

            response = response.json()
            assert len(response["errors"]) == 1, response.get(
                "errors", "'errors' not found in response"
            )
            assert response["meta"]["data_returned"] == 0, response.get(
                "meta", "'meta' not found in response"
            )

            error = response["errors"][0]
            assert str(expected_status) == error["status"], error
            assert expected_title == error["title"], error

            if expected_detail is None:
                expected_detail = "Error trying to process rule "
                assert error["detail"].startswith(expected_detail), (
                    "No expected_detail provided and the error did not start with a standard Lark "
                    "error message."
                )
            else:
                assert expected_detail == error["detail"], error

        except Exception:
            print(
                f"Request attempted:\n{used_client.base_url}{used_client.version}"
                f"{request}"
            )
            if response:
                print(f"\nCaptured response:\n{response}")
            raise

    return inner
