""" This submodule contains utility methods and models
used by the validator. The two main features being:

1. The `@test_case` decorator can be used to decorate validation
   methods and performs error handling, output and logging of test
   successes and failures.
2. The patched `Validator` versions allow for stricter validation
   of server responses. The standard response classes allow entries
   to be provided as bare dictionaries, whilst these patched classes
   force them to be validated with the corresponding entry models
   themselves.

"""

import time
import sys
import urllib.parse
import dataclasses
import traceback as tb
from typing import List, Optional, Dict, Any, Callable, Tuple

try:
    import simplejson as json
except ImportError:
    import json

import requests
from pydantic import Field, ValidationError

from optimade.models.optimade_json import Success
from optimade.models import (
    ResponseMeta,
    EntryResource,
    LinksResource,
    ReferenceResource,
    StructureResource,
)


class ResponseError(Exception):
    """This exception should be raised for a manual hardcoded test failure."""


class InternalError(Exception):
    """This exception should be raised when validation throws an unexpected error.
    These should be counted separately from `ResponseError`'s and `ValidationError`'s.

    """


def print_warning(string, **kwargs):
    """Print but angry."""
    print(f"\033[93m{string}\033[0m", **kwargs)


def print_notify(string, **kwargs):
    """Print but louder."""
    print(f"\033[94m\033[1m{string}\033[0m", **kwargs)


def print_failure(string, **kwargs):
    """Print but sad."""
    print(f"\033[91m\033[1m{string}\033[0m", **kwargs)


def print_success(string, **kwargs):
    """Print but happy."""
    print(f"\033[92m\033[1m{string}\033[0m", **kwargs)


@dataclasses.dataclass
class ValidatorResults:
    """A dataclass to store and print the validation results."""

    success_count: int = 0
    failure_count: int = 0
    internal_failure_count: int = 0
    optional_success_count: int = 0
    optional_failure_count: int = 0
    failure_messages: List[Tuple[str, str]] = dataclasses.field(default_factory=list)
    internal_failure_messages: List[Tuple[str, str]] = dataclasses.field(
        default_factory=list
    )
    optional_failure_messages: List[Tuple[str, str]] = dataclasses.field(
        default_factory=list
    )
    verbosity: int = 0

    def add_success(self, summary: str, success_type: Optional[str] = None):
        """Register a validation success to the results class.

        Parameters:
            summary: A summary of the success to be printed.
            success_type: Either `None` or `"optional"` depending on the
                type of the check.

        """
        success_types = (None, "optional")
        if success_type not in success_types:
            raise RuntimeError(
                f"`success_type` must be one of {success_types}, not {success_type}."
            )

        if success_type is None:
            self.success_count += 1
        elif success_type == "optional":
            self.optional_success_count += 1

        message = f"✔: {summary}"
        pretty_print = print if success_type == "optional" else print_success

        if self.verbosity > 0:
            pretty_print(message)
        elif self.verbosity == 0:
            pretty_print(".", end="", flush=True)

    def add_failure(
        self, summary: str, message: str, failure_type: Optional[str] = None
    ):
        """Register a validation failure to the results class with
        corresponding summary, message and type.

        Parameters:
            summary: Short error message.
            message: Full error message, potentially containing a traceback.
            failure_type: Either `None`, `"internal"` or `"optional"`
                depending on the type of check that was failed.

        """
        failure_types = (None, "internal", "optional")
        if failure_type not in failure_types:
            raise RuntimeError(
                f"`failure_type` must be one of {failure_types}, not {failure_type}."
            )

        if failure_type is None:
            self.failure_count += 1
            self.failure_messages.append((summary, message))
        elif failure_type == "internal":
            self.internal_failure_count += 1
            self.internal_failure_messages.append((summary, message))
        elif failure_type == "optional":
            self.optional_failure_count += 1
            self.optional_failure_messages.append((summary, message))

        pprint_types = {
            "internal": (print_notify, print_warning),
            "optional": (print, print),
        }
        pprint, warning_pprint = pprint_types.get(
            failure_type, (print_failure, print_warning)
        )

        symbol = "!" if failure_type == "internal" else "✖"
        if self.verbosity == 0:
            pprint(symbol, end="", flush=True)
        elif self.verbosity > 0:
            pprint(f"{symbol}: {summary}")
            for line in message.split("\n"):
                warning_pprint(f"\t{line}")


class Client:  # pragma: no cover
    def __init__(
        self, base_url: str, max_retries: int = 5, headers: Dict[str, str] = None
    ) -> None:
        """Initialises the Client with the given `base_url` without testing
        if it is valid.

        Parameters:
            base_url (str): the base URL of the optimade implementation, including
                request protocol (e.g. `'http://'`) and API version number if necessary.

                Examples:

                - `'http://example.org/optimade/v1'`,
                - `'www.crystallography.net/cod-test/optimade/v0.10.0/'`

                Note: A maximum of one slash ("/") is allowed as the last character.

            max_retries: The maximum number of attempts to make for each query.
            headers: Dictionary of additional headers to add to every request.

        """
        self.base_url = base_url
        self.last_request = None
        self.response = None
        self.max_retries = max_retries
        self.headers = headers or {}

    def get(self, request: str):
        """Makes the given request, with a number of retries if being rate limited. The
        request will be prepended with the `base_url` unless the request appears to be an
        absolute URL (i.e. starts with `http://` or `https://`).

        Parameters:
            request (str): the request to make against the base URL of this client.

        Returns:
            response (requests.models.Response): the response from the server.

        Raises:
            SystemExit: if there is no response from the server, or if the URL is invalid.
            ResponseError: if the server does not respond with a non-429 status code within
                the `MAX_RETRIES` attempts.

        """
        if urllib.parse.urlparse(request, allow_fragments=True).scheme:
            self.last_request = request
        else:
            if request and not request.startswith("/"):
                request = f"/{request}"
            self.last_request = f"{self.base_url}{request}"

        status_code = None
        retries = 0
        # probably a smarter way to do this with requests, but their documentation 404's...
        while retries < self.max_retries:
            retries += 1
            try:
                self.response = requests.get(self.last_request, headers=self.headers)
            except requests.exceptions.ConnectionError as exc:
                sys.exit(
                    f"{exc.__class__.__name__}: No response from server at {self.last_request}, please check the URL."
                )
            except requests.exceptions.MissingSchema:
                sys.exit(
                    f"Unable to make request on {self.last_request}, did you mean http://{self.last_request}?"
                )
            status_code = self.response.status_code
            if status_code != 429:
                break

            time.sleep(1)

        else:
            raise ResponseError("Hit max (manual) retries on request.")

        return self.response


def test_case(test_fn: Callable[[Any], Tuple[Any, str]]):
    """Wrapper for test case functions, which pretty-prints any errors
    depending on verbosity level, collates the number and severity of
    test failures, returns the response and summary string to the caller.
    Any additional positional or keyword arguments are passed directly
    to `test_fn`. The wrapper will intercept the named arguments
    `optional`, `multistage` and `request` and interpret them according
    to the docstring for `wrapper(...)` below.

    Parameters:
        test_fn: Any function that returns an object and a message to
            print upon success. The function should raise a `ResponseError`,
            `ValidationError` or a `ManualValidationError` if the test
            case has failed. The function can return `None` to indicate
            that the test was not appropriate and should be ignored.

    """
    from functools import wraps

    @wraps(test_fn)
    def wrapper(
        validator,
        *args,
        request: str = None,
        optional: bool = False,
        multistage: bool = False,
        **kwargs,
    ):
        """Wraps a function or validator method and handles
        success, failure and output depending on the keyword
        arguments passed.

        Arguments:
            validator: The validator object to accumulate errors/counters.
            *args: Positional arguments passed to the test function.
            request: Description of the request made by the wrapped
                function (e.g. a URL or a summary).
            optional: Whether or not to treat the test as optional.
            multistage: If `True`, no output will be printed for this test,
                and it will not increment the success counter. Errors will be
                handled in the normal way. This can be used to avoid flooding
                the output for mutli-stage tests.
            **kwargs: Extra named arguments passed to the test function.

        """
        try:
            try:
                if optional and not validator.run_optional_tests:
                    result = None
                    msg = "skipping optional"
                else:
                    result, msg = test_fn(validator, *args, **kwargs)

            except (json.JSONDecodeError, ResponseError, ValidationError) as exc:
                msg = f"{exc.__class__.__name__}: {exc}"
                raise exc
            except Exception as exc:
                msg = f"{exc.__class__.__name__}: {exc}"
                raise InternalError(msg)

        # Catch SystemExit and KeyboardInterrupt explicitly so that we can pass
        # them to the finally block, where they are immediately raised
        except (Exception, SystemExit, KeyboardInterrupt) as exc:
            result = exc
            traceback = tb.format_exc()

        finally:
            # This catches the case of the Client throwing a SystemExit if the server
            # did not respond, the case of the validator "fail-fast"'ing and throwing
            # a SystemExit below, and the case of the user interrupting the process manually
            if isinstance(result, (SystemExit, KeyboardInterrupt)):
                raise result

            display_request = None
            try:
                display_request = validator.client.last_request
            except AttributeError:
                pass
            if display_request is None:
                display_request = validator.base_url
                if request is not None:
                    display_request += "/" + request

            request = display_request

            # If the result was None, return it here and ignore statuses
            if result is None:
                return result, msg

            if not isinstance(result, Exception):
                if not multistage:
                    success_type = "optional" if optional else None
                    validator.results.add_success(f"{request} - {msg}", success_type)
            else:
                request = request.replace("\n", "")
                message = msg.split("\n")
                if validator.verbosity > 1:
                    # ValidationErrors from pydantic already include very detailed errors
                    # that get duplicated in the traceback
                    if not isinstance(result, ValidationError):
                        message += traceback.split("\n")

                message = "\n".join(message)

                if isinstance(result, InternalError):
                    summary = (
                        f"{request} - {test_fn.__name__} - failed with internal error"
                    )
                    failure_type = "internal"
                else:
                    summary = f"{request} - {test_fn.__name__} - failed with error"
                    failure_type = "optional" if optional else None

                validator.results.add_failure(
                    summary, message, failure_type=failure_type
                )

                # set failure result to None as this is expected by other functions
                result = None

                if validator.fail_fast and not optional:
                    validator.print_summary()
                    raise SystemExit

            # Reset the client request so that it can be properly
            # displayed if the next request fails
            if not multistage:
                validator.client.last_request = None

            return result, msg

    return wrapper


class ValidatorLinksResponse(Success):
    meta: ResponseMeta = Field(...)
    data: List[LinksResource] = Field(...)


class ValidatorEntryResponseOne(Success):
    meta: ResponseMeta = Field(...)
    data: EntryResource = Field(...)
    included: Optional[List[Dict[str, Any]]] = Field(None)


class ValidatorEntryResponseMany(Success):
    meta: ResponseMeta = Field(...)
    data: List[EntryResource] = Field(...)
    included: Optional[List[Dict[str, Any]]] = Field(None)


class ValidatorReferenceResponseOne(ValidatorEntryResponseOne):
    data: ReferenceResource = Field(...)


class ValidatorReferenceResponseMany(ValidatorEntryResponseMany):
    data: List[ReferenceResource] = Field(...)


class ValidatorStructureResponseOne(ValidatorEntryResponseOne):
    data: StructureResource = Field(...)


class ValidatorStructureResponseMany(ValidatorEntryResponseMany):
    data: List[StructureResource] = Field(...)
