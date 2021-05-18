import pytest
from optimade.validator.utils import test_case as validator_test_case
from optimade.validator.utils import ResponseError
from optimade.validator.validator import ImplementationValidator

try:
    import simplejson as json
except ImportError:
    import json


@validator_test_case
def dummy_test_case(_, returns, raise_exception=None):
    """Dummy function that returns what is passed it,
    optionally raising an exception.

    """
    if raise_exception:
        raise raise_exception

    return returns


def test_normal_test_case():
    """Check test_case under normal conditions."""
    validator = ImplementationValidator(base_url="http://example.org", verbosity=0)

    output = dummy_test_case(validator, ([1, 2, 3], "message"), request="test_request")
    assert validator.results.success_count == 1
    assert validator.results.optional_success_count == 0
    assert validator.results.failure_count == 0
    assert validator.results.optional_failure_count == 0
    assert validator.results.internal_failure_count == 0
    assert output[0] == [1, 2, 3]
    assert output[1] == "message"


def test_optional_test_case():
    """Check test_case for optional case."""
    validator = ImplementationValidator(base_url="http://example.org", verbosity=0)

    output = dummy_test_case(
        validator, ("string response", "message"), request="test_request", optional=True
    )
    assert validator.results.success_count == 0
    assert validator.results.optional_success_count == 1
    assert validator.results.failure_count == 0
    assert validator.results.optional_failure_count == 0
    assert validator.results.internal_failure_count == 0
    assert output[0] == "string response"
    assert output[1] == "message"


def test_ignored_test_case():
    """Check test_case is ignored when receiving `None`."""
    validator = ImplementationValidator(base_url="http://example.org", verbosity=0)

    # Test returns None, so should not increment success/failure
    output = dummy_test_case(validator, (None, "message"), request="test_request")
    assert validator.results.success_count == 0
    assert validator.results.optional_success_count == 0
    assert validator.results.failure_count == 0
    assert validator.results.optional_failure_count == 0
    assert validator.results.internal_failure_count == 0
    assert output[0] is None
    assert output[1] == "message"


def test_skip_optional_test_case():
    """Check test_case skips a test when optional."""
    validator = ImplementationValidator(
        base_url="http://example.org", verbosity=0, run_optional_tests=False
    )

    # Test is optional and validator should not be running optional tests, so it should
    # return hardcoded (None, "skipping optional").
    output = dummy_test_case(
        validator, ({"test": "dict"}, "message"), request="test_request", optional=True
    )
    assert validator.results.success_count == 0
    assert validator.results.optional_success_count == 0
    assert validator.results.failure_count == 0
    assert validator.results.optional_failure_count == 0
    assert validator.results.internal_failure_count == 0
    assert output[0] is None
    assert output[1] == "skipping optional"

    # Now check that the same test returns the correct values when not marked as optional
    output = dummy_test_case(
        validator, ({"test": "dict"}, "message"), request="test_request", optional=False
    )
    assert validator.results.success_count == 1
    assert validator.results.optional_success_count == 0
    assert validator.results.failure_count == 0
    assert validator.results.optional_failure_count == 0
    assert validator.results.internal_failure_count == 0
    assert output[0] == {"test": "dict"}
    assert output[1] == "message"


def test_expected_failure_test_case():
    """Check test_case reports a "failure" when `ResponseError` is raised."""
    validator = ImplementationValidator(base_url="http://example.org", verbosity=0)

    # Test is optional and validator should not be running optional tests, so it should
    # return hardcoded (None, "skipping optional").
    output = dummy_test_case(
        validator,
        ({"test": "dict"}, "message"),
        request="test_request",
        raise_exception=ResponseError("Dummy error"),
    )
    assert validator.results.success_count == 0
    assert validator.results.optional_success_count == 0
    assert validator.results.failure_count == 1
    assert validator.results.optional_failure_count == 0
    assert validator.results.internal_failure_count == 0

    assert output[0] is None
    assert output[1] == "ResponseError: Dummy error"

    assert (
        validator.results.failure_messages[-1][0]
        == "http://example.org/test_request - dummy_test_case - failed with error"
    )
    assert validator.results.failure_messages[-1][1] == "ResponseError: Dummy error"

    output = dummy_test_case(
        validator,
        ({"test": "dict"}, "message"),
        request="test_request",
        raise_exception=ResponseError("Dummy error"),
        optional=True,
    )
    assert validator.results.success_count == 0
    assert validator.results.optional_success_count == 0
    assert validator.results.failure_count == 1
    assert validator.results.optional_failure_count == 1
    assert validator.results.internal_failure_count == 0

    assert output[0] is None
    assert output[1] == "ResponseError: Dummy error"

    assert (
        validator.results.optional_failure_messages[-1][0]
        == "http://example.org/test_request - dummy_test_case - failed with error"
    )
    assert (
        validator.results.optional_failure_messages[-1][1]
        == "ResponseError: Dummy error"
    )

    output = dummy_test_case(
        validator,
        ({"test": "dict"}, "message"),
        request="test_request",
        raise_exception=json.JSONDecodeError("Dummy JSON error", "{}", 0),
        optional=True,
    )
    assert validator.results.success_count == 0
    assert validator.results.optional_success_count == 0
    assert validator.results.failure_count == 1
    assert validator.results.optional_failure_count == 2
    assert validator.results.internal_failure_count == 0

    assert output[0] is None
    assert output[1] == "JSONDecodeError: Dummy JSON error: line 1 column 1 (char 0)"
    assert (
        validator.results.optional_failure_messages[-1][0]
        == "http://example.org/test_request - dummy_test_case - failed with error"
    )
    assert (
        validator.results.optional_failure_messages[-1][1]
        == "JSONDecodeError: Dummy JSON error: line 1 column 1 (char 0)"
    )


def test_unexpected_failure_test_case():
    """Check test_case catches unexpected errors as internal failures."""
    validator = ImplementationValidator(base_url="http://example.org", verbosity=0)

    # Raise some unexpected exception and make sure it is logged as an internal error
    output = dummy_test_case(
        validator,
        ({"test": "dict"}, "message"),
        request="test_request",
        raise_exception=FileNotFoundError("Unexpected error"),
    )
    assert validator.results.success_count == 0
    assert validator.results.optional_success_count == 0
    assert validator.results.failure_count == 0
    assert validator.results.optional_failure_count == 0
    assert validator.results.internal_failure_count == 1

    assert output[0] is None
    assert output[1] == "FileNotFoundError: Unexpected error"
    assert (
        validator.results.internal_failure_messages[-1][0]
        == "http://example.org/test_request - dummy_test_case - failed with internal error"
    )
    assert (
        validator.results.internal_failure_messages[-1][1]
        == "FileNotFoundError: Unexpected error"
    )

    output = dummy_test_case(
        validator,
        ({"test": "dict"}, "message"),
        request="test_request",
        raise_exception=FileNotFoundError("Unexpected error"),
        optional=True,
    )
    assert validator.results.success_count == 0
    assert validator.results.optional_success_count == 0
    assert validator.results.failure_count == 0
    assert validator.results.optional_failure_count == 0
    assert validator.results.internal_failure_count == 2

    assert output[0] is None
    assert output[1] == "FileNotFoundError: Unexpected error"
    assert (
        validator.results.internal_failure_messages[-1][0]
        == "http://example.org/test_request - dummy_test_case - failed with internal error"
    )
    assert (
        validator.results.internal_failure_messages[-1][1]
        == "FileNotFoundError: Unexpected error"
    )


def test_multistage_test_case():
    """Check test_case's `multistage` functionality works as expected."""
    validator = ImplementationValidator(base_url="http://example.org", verbosity=0)

    # Test that multistage requests do nothing but return unless they've failed
    output = dummy_test_case(
        validator,
        ({"test": "dict"}, "message"),
        request="test_request",
        multistage=True,
    )
    assert validator.results.success_count == 0
    assert validator.results.optional_success_count == 0
    assert validator.results.failure_count == 0
    assert validator.results.optional_failure_count == 0
    assert validator.results.internal_failure_count == 0

    assert output[0] == {"test": "dict"}
    assert output[1] == "message"

    output = dummy_test_case(
        validator,
        ({"test": "dict"}, "message"),
        request="test_request",
        raise_exception=ResponseError("Stage of test failed"),
        multistage=True,
    )
    assert validator.results.success_count == 0
    assert validator.results.optional_success_count == 0
    assert validator.results.failure_count == 1
    assert validator.results.optional_failure_count == 0
    assert validator.results.internal_failure_count == 0

    assert output[0] is None
    assert output[1] == "ResponseError: Stage of test failed"
    assert (
        validator.results.failure_messages[-1][0]
        == "http://example.org/test_request - dummy_test_case - failed with error"
    )
    assert (
        validator.results.failure_messages[-1][1]
        == "ResponseError: Stage of test failed"
    )


def test_fail_fast_test_case():
    """Check test_case's `fail_fast` feature works as intended."""
    validator = ImplementationValidator(
        base_url="http://example.org", verbosity=0, fail_fast=True
    )

    # Check that optional failures do not trigger fail fast
    output = dummy_test_case(
        validator,
        ({"test": "dict"}, "message"),
        request="test_request",
        raise_exception=ResponseError("Optional test failed"),
        optional=True,
    )
    assert validator.results.success_count == 0
    assert validator.results.optional_success_count == 0
    assert validator.results.failure_count == 0
    assert validator.results.optional_failure_count == 1
    assert validator.results.internal_failure_count == 0

    assert output[0] is None
    assert output[1] == "ResponseError: Optional test failed"
    assert validator.results.optional_failure_messages[-1][0] == (
        "http://example.org/test_request - dummy_test_case - failed with error"
    )
    assert (
        validator.results.optional_failure_messages[-1][1]
        == "ResponseError: Optional test failed"
    )

    # Check that the same non-optional failures do trigger fail fast
    with pytest.raises(SystemExit):
        output = dummy_test_case(
            validator,
            ({"test": "dict"}, "message"),
            request="test_request",
            raise_exception=ResponseError("Non-optional test failed"),
            optional=False,
        )
    assert validator.results.success_count == 0
    assert validator.results.optional_success_count == 0
    assert validator.results.failure_count == 1
    assert validator.results.optional_failure_count == 1
    assert validator.results.internal_failure_count == 0
    assert validator.results.failure_messages[-1][0] == (
        "http://example.org/test_request - dummy_test_case - failed with error"
    )
    assert (
        validator.results.failure_messages[-1][1]
        == "ResponseError: Non-optional test failed"
    )

    # Check that an internal error also triggers fast
    with pytest.raises(SystemExit):
        output = dummy_test_case(
            validator,
            ({"test": "dict"}, "message"),
            request="test_request",
            raise_exception=FileNotFoundError("Internal error"),
        )
    assert validator.results.success_count == 0
    assert validator.results.optional_success_count == 0
    assert validator.results.failure_count == 1
    assert validator.results.optional_failure_count == 1
    assert validator.results.internal_failure_count == 1
    assert validator.results.internal_failure_messages[-1][0] == (
        "http://example.org/test_request - dummy_test_case - failed with internal error"
    )
    assert (
        validator.results.internal_failure_messages[-1][1]
        == "FileNotFoundError: Internal error"
    )


def test_that_system_exit_is_fatal_in_test_case():
    """Check that test_case treats `SystemExit` as fatal."""
    validator = ImplementationValidator(
        base_url="http://example.org", verbosity=0, fail_fast=False
    )

    with pytest.raises(SystemExit, match="Fatal error"):
        dummy_test_case(
            validator,
            ({"test": "dict"}, "message"),
            request="test_request",
            raise_exception=SystemExit("Fatal error"),
            optional=True,
        )

    assert validator.results.success_count == 0
    assert validator.results.optional_success_count == 0
    assert validator.results.failure_count == 0
    assert validator.results.optional_failure_count == 0
    assert validator.results.internal_failure_count == 0


def test_versions_test_cases():
    """Check the `/versions` test cases."""
    from requests import Response
    from functools import partial

    unversioned_base_url = "https://example.org"
    versioned_base_url = unversioned_base_url + "/v1"

    def monkey_patched_get_endpoint(
        url,
        expected_status_code=200,
        content=b"version\n1",
        content_type="text/csv;header=present",
        **kwargs
    ):
        r = Response()
        if expected_status_code == 200:
            r._content = content
            r.headers["content-type"] = content_type
            r.status_code = 200
        else:
            r.status_code = 404

        gets.append(url)

        return r, None

    # Test that the versioned base URL correctly tests the unversioned and then resets
    validator = ImplementationValidator(base_url=versioned_base_url, verbosity=5)
    gets = []
    validator._get_endpoint = monkey_patched_get_endpoint
    validator._test_versions_endpoint()
    assert len(gets) == 2
    assert validator.client.base_url == versioned_base_url
    assert validator.results.success_count == 1
    assert validator.results.optional_success_count == 2
    assert validator.results.failure_count == 0

    # Test that the unversioned base URL correctly tests just the unversioned URL
    validator = ImplementationValidator(base_url=unversioned_base_url, verbosity=0)
    gets = []
    validator._get_endpoint = monkey_patched_get_endpoint
    validator._test_versions_endpoint()
    assert len(gets) == 1
    assert validator.client.base_url == unversioned_base_url
    assert validator.results.success_count == 1
    assert validator.results.optional_success_count == 2
    assert validator.results.failure_count == 0

    # Test that bad content successfully triggers failures
    bad_content = (b"versions\n1", b"version\n", b"version\n1.1")
    for content in bad_content:
        validator = ImplementationValidator(base_url=versioned_base_url, verbosity=0)
        validator._get_endpoint = partial(monkey_patched_get_endpoint, content=content)
        validator._test_versions_endpoint()
        assert validator.client.base_url == versioned_base_url
        assert validator.results.success_count == 0
        assert validator.results.failure_count == 1
        assert validator.results.optional_failure_count == 0

    # Test that missing content-type header triggers a hard failure
    validator = ImplementationValidator(base_url=versioned_base_url, verbosity=0)
    validator._get_endpoint = partial(monkey_patched_get_endpoint, content_type="")
    validator._test_versions_endpoint()
    assert validator.client.base_url == versioned_base_url
    assert validator.results.success_count == 0
    assert validator.results.failure_count == 1
    assert validator.results.optional_failure_count == 0

    # Test that bad content-type headers successfully trigger *optional* failures
    bad_content_type = (
        ("text/csv", 1),
        ("text/plain", 1),
        ("header=present", 1),
        ("x;y", 2),
        ("application/json;charset=utf-8", 2),
    )
    for content_type, num_errors in bad_content_type:
        validator = ImplementationValidator(base_url=versioned_base_url, verbosity=0)
        validator._get_endpoint = partial(
            monkey_patched_get_endpoint, content_type=content_type
        )
        validator._test_versions_endpoint()
        assert validator.client.base_url == versioned_base_url
        assert validator.results.success_count == 1
        assert validator.results.failure_count == 0
        assert validator.results.optional_failure_count == num_errors
