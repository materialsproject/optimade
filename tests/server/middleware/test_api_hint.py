"""Test HandleApiHint middleware and the `api_hint` query parameter"""
import pytest
from urllib.parse import unquote

from optimade.server.exceptions import VersionNotSupported
from optimade.server.middleware import HandleApiHint


def test_correct_api_hint(both_clients, check_response):
    """Check correct value for `api_hint` works fine"""
    from optimade.server.routers.utils import BASE_URL_PREFIXES

    links_id = "index"
    major_version = BASE_URL_PREFIXES["major"][1:]  # Remove prefixed `/`
    query_url = f'/links?api_hint={major_version}&filter=id="{links_id}"'

    check_response(
        request=query_url,
        expected_ids=[links_id],
        server=both_clients,
    )


def test_incorrect_api_hint(both_clients, check_error_response):
    """Check incorrect value for `api_hint` raises VersionNotSupported"""
    from optimade.server.routers.utils import BASE_URL_PREFIXES

    links_id = "index"
    incorrect_version = int(BASE_URL_PREFIXES["major"][len("/v") :]) + 1
    incorrect_version = f"v{incorrect_version}"
    query_url = f'/links?api_hint={incorrect_version}&filter=id="{links_id}"'

    with pytest.raises(VersionNotSupported):
        check_error_response(
            request=query_url,
            expected_status=553,
            expected_title="Version Not Supported",
            expected_detail=(
                f"The provided `api_hint` ({incorrect_version!r}) is not supported by "
                "this implementation. Supported versions include: "
                f"{', '.join(BASE_URL_PREFIXES.values())}"
            ),
            server=both_clients,
        )


def test_url_changes(both_clients, get_good_response):
    """Check `api_hint` redirects request from unversioned base URL to versioned base URL

    Also, the `api_hint` query parameter should be removed.
    """
    from optimade.server.routers.utils import BASE_URL_PREFIXES

    links_id = "index"
    major_version = BASE_URL_PREFIXES["major"][1:]  # Remove prefixed `/`
    query_url = f'/links?filter=id="{links_id}"&api_hint={major_version}'

    response = get_good_response(query_url, server=both_clients, return_json=False)

    assert (
        unquote(response.url)
        == f"{both_clients.base_url}{BASE_URL_PREFIXES['major']}{query_url.split('&')[0]}"
    )

    # Now to make sure the redirect would not happen when leaving out `api_hint`
    query_url = f'/links?filter=id="{links_id}"'

    response = get_good_response(query_url, server=both_clients, return_json=False)

    assert unquote(response.url) == f"{both_clients.base_url}{query_url}"


def test_is_versioned_base_url(both_clients):
    """Check is_versioned_base_url method"""
    from optimade.server.config import CONFIG
    from optimade.server.routers.utils import BASE_URL_PREFIXES

    valid_version = BASE_URL_PREFIXES["major"]

    versioned_base_url = f"{CONFIG.base_url}{valid_version}/info"
    assert HandleApiHint.is_versioned_base_url(versioned_base_url)

    unversioned_base_url = f"{CONFIG.base_url}/info"
    assert not HandleApiHint.is_versioned_base_url(unversioned_base_url)

    org_base_url = CONFIG.base_url
    try:
        CONFIG.base_url = f"{both_clients.base_url}{valid_version}/optimade"

        embedded_versioned_base_url = f"{CONFIG.base_url}{valid_version}/info"
        assert HandleApiHint.is_versioned_base_url(embedded_versioned_base_url)

        embedded_unversioned_base_url = f"{CONFIG.base_url}/info"
        assert not HandleApiHint.is_versioned_base_url(embedded_unversioned_base_url)
    finally:
        if org_base_url:
            CONFIG.base_url = org_base_url
        else:
            CONFIG.base_url = None


def test_handle_api_hint():
    """Check handle_api_hint method"""
    from optimade.server.routers.utils import BASE_URL_PREFIXES
    from optimade.server.warnings import FieldValueNotRecognized, TooManyValues

    api_hint = ["v1", "v2"]
    warning_detail = "`api_hint` should only be supplied once, with a single value."
    with pytest.warns(TooManyValues, match=warning_detail):
        assert HandleApiHint.handle_api_hint(api_hint) is None

    api_hint = BASE_URL_PREFIXES["patch"][1:]
    warning_detail = f"{api_hint!r} is not recognized as a valid `api_hint` value."
    with pytest.warns(FieldValueNotRecognized, match=warning_detail):
        assert HandleApiHint.handle_api_hint([api_hint]) is None

    for version_part in ("major", "minor"):
        api_hint = BASE_URL_PREFIXES[version_part][1:]
        assert (
            HandleApiHint.handle_api_hint([api_hint]) == BASE_URL_PREFIXES[version_part]
        )

    with pytest.raises(VersionNotSupported):
        api_hint = f"v{int(BASE_URL_PREFIXES['major'][len('/v'):]) + 1}"
        HandleApiHint.handle_api_hint([api_hint])

    api_hint = "v0"
    assert HandleApiHint.handle_api_hint([api_hint]) == BASE_URL_PREFIXES["major"]

    api_hint = f"{BASE_URL_PREFIXES['major'][1:]}.{int(BASE_URL_PREFIXES['minor'].split('.')[-1]) + 1}"
    assert HandleApiHint.handle_api_hint([api_hint]) == BASE_URL_PREFIXES["major"]


def test_api_hint_with_versioned_base_url(get_good_response, both_clients):
    """Make sure a `QueryParamNotUsed` warning is included for requests
    with `api_hint` to versioned base URLs."""
    from optimade.server.routers.utils import BASE_URL_PREFIXES
    from optimade.server.warnings import QueryParamNotUsed

    valid_version = BASE_URL_PREFIXES["major"]
    request = f"{valid_version}/info?api_hint={valid_version[1:]}"
    warning_detail = (
        f"`api_hint` provided with value {valid_version[1:]!r} for a versioned base URL. "
        "In accordance with the specification, this will not be handled by the implementation."
    )

    with pytest.warns(QueryParamNotUsed, match=warning_detail):
        response = get_good_response(request, both_clients)

    assert "warnings" in response.get("meta", {})
    assert len(response["meta"]["warnings"]) == 1
    assert response["meta"]["warnings"][0].get("detail", "") == warning_detail
    assert (
        response["meta"]["warnings"][0].get("title", "") == QueryParamNotUsed.__name__
    )


def test_api_hint_warnings(get_good_response, both_clients):
    """Make sure warnings are added to the response"""
    from optimade.server.routers.utils import BASE_URL_PREFIXES
    from optimade.server.warnings import FieldValueNotRecognized, TooManyValues

    requests = ["/info?api_hint=v1,v2", "/info?api_hint=v1&api_hint=v2"]
    warning_detail = "`api_hint` should only be supplied once, with a single value."
    for request in requests:
        with pytest.warns(TooManyValues, match=warning_detail):
            response = get_good_response(request, both_clients)

        assert "warnings" in response.get("meta", {})
        assert len(response["meta"]["warnings"]) == 1
        assert response["meta"]["warnings"][0].get("detail", "") == warning_detail
        assert (
            response["meta"]["warnings"][0].get("title", "") == TooManyValues.__name__
        )

    api_hint = BASE_URL_PREFIXES["patch"][1:]
    request = f"/info?api_hint={api_hint}"
    warning_detail = f"{api_hint!r} is not recognized as a valid `api_hint` value."
    with pytest.warns(FieldValueNotRecognized, match=warning_detail):
        response = get_good_response(request, both_clients)

    assert "warnings" in response.get("meta", {})
    assert len(response["meta"]["warnings"]) == 1
    assert response["meta"]["warnings"][0].get("detail", "") == warning_detail
    assert (
        response["meta"]["warnings"][0].get("title", "")
        == FieldValueNotRecognized.__name__
    )
