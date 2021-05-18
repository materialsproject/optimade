"""Test CheckWronglyVersionedBaseUrls middleware"""
import urllib.parse

import pytest

from optimade.server.exceptions import VersionNotSupported
from optimade.server.middleware import CheckWronglyVersionedBaseUrls


def test_wrong_version(both_clients):
    """If a non-supported versioned base URL is passed, `553 Version Not Supported` should be returned"""
    from optimade.server.config import CONFIG

    version = "/v0"
    urls = (
        f"{CONFIG.base_url}{version}/info",
        f"{CONFIG.base_url}{version}",
    )

    for url in urls:
        with pytest.raises(VersionNotSupported):
            CheckWronglyVersionedBaseUrls(both_clients.app).check_url(
                urllib.parse.urlparse(url)
            )


def test_wrong_version_json_response(check_error_response, both_clients):
    """If a non-supported versioned base URL is passed, `553 Version Not Supported` should be returned

    A specific JSON response should also occur.
    """
    from optimade.server.routers.utils import BASE_URL_PREFIXES

    version = "/v0"
    request = f"{version}/info"
    with pytest.raises(VersionNotSupported):
        check_error_response(
            request,
            expected_status=553,
            expected_title="Version Not Supported",
            expected_detail=(
                f"The parsed versioned base URL {version!r} from '{both_clients.base_url}{request}' is not supported by this implementation. "
                f"Supported versioned base URLs are: {', '.join(BASE_URL_PREFIXES.values())}"
            ),
            server=both_clients,
        )


def test_multiple_versions_in_path(both_clients):
    """If another version is buried in the URL path, only the OPTIMADE versioned URL path part should be recognized."""
    from optimade.server.config import CONFIG
    from optimade.server.routers.utils import BASE_URL_PREFIXES

    non_valid_version = "/v0.5"
    org_base_url = CONFIG.base_url

    try:
        CONFIG.base_url = f"https://example.org{non_valid_version}/my_database/optimade"

        for valid_version_prefix in BASE_URL_PREFIXES.values():
            url = f"{CONFIG.base_url}{valid_version_prefix}/info"
            CheckWronglyVersionedBaseUrls(both_clients.app).check_url(
                urllib.parse.urlparse(url)
            )

        # Test also that a non-valid OPTIMADE version raises
        url = f"{CONFIG.base_url}/v0/info"
        with pytest.raises(VersionNotSupported):
            CheckWronglyVersionedBaseUrls(both_clients.app).check_url(
                urllib.parse.urlparse(url)
            )
    finally:
        if org_base_url:
            CONFIG.base_url = org_base_url
        else:
            CONFIG.base_url = None


def test_versioned_base_urls(both_clients):
    """Test the middleware does not wrongly catch requests to versioned base URLs"""
    from optimade.server.config import CONFIG
    from optimade.server.routers.utils import BASE_URL_PREFIXES

    for request in BASE_URL_PREFIXES.values():
        CheckWronglyVersionedBaseUrls(both_clients.app).check_url(
            urllib.parse.urlparse(f"{CONFIG.base_url}{request}")
        )
