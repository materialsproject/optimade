"""
Custom ASGI app middleware.

These middleware are based on [Starlette](https://www.starlette.io)'s `BaseHTTPMiddleware`.
See the specific Starlette [documentation page](https://www.starlette.io/middleware/) for more
information on it's middleware implementation.
"""
import re
from typing import Optional, IO, Type, Generator, List, Union, Tuple
import urllib.parse
import warnings

try:
    import simplejson as json
except ImportError:
    import json

from starlette.datastructures import URL as StarletteURL
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse, StreamingResponse

from optimade.models import Warnings
from optimade.server.config import CONFIG
from optimade.server.exceptions import BadRequest, VersionNotSupported
from optimade.server.warnings import (
    FieldValueNotRecognized,
    OptimadeWarning,
    QueryParamNotUsed,
    TooManyValues,
)
from optimade.server.routers.utils import get_base_url, BASE_URL_PREFIXES


class EnsureQueryParamIntegrity(BaseHTTPMiddleware):
    """Ensure all query parameters are followed by an equal sign (`=`)."""

    @staticmethod
    def check_url(url_query: str) -> set:
        """Check parsed URL query part for parameters not followed by `=`.

        URL query parameters are considered to be split by ampersand (`&`)
        and semi-colon (`;`).

        Parameters:
            url_query: The raw urllib-parsed query part.

        Raises:
            BadRequest: If a query parameter does not come with a value.

        Returns:
            The set of individual query parameters and their values.

            This is mainly for testing and not actually neeeded by the middleware,
            since if the URL exhibits an invalid query part a `400 Bad Request`
            response will be returned.

        """
        queries_amp = set(url_query.split("&"))
        queries = set()
        for query in queries_amp:
            queries.update(set(query.split(";")))
        for query in queries:
            if "=" not in query and query != "":
                raise BadRequest(
                    detail="A query parameter without an equal sign (=) is not supported by this server"
                )
        return queries  # Useful for testing

    async def dispatch(self, request: Request, call_next):
        parsed_url = urllib.parse.urlsplit(str(request.url))
        if parsed_url.query:
            self.check_url(parsed_url.query)
        response = await call_next(request)
        return response


class CheckWronglyVersionedBaseUrls(BaseHTTPMiddleware):
    """If a non-supported versioned base URL is supplied return `553 Version Not Supported`."""

    @staticmethod
    def check_url(url: StarletteURL):
        """Check URL path for versioned part.

        Parameters:
            url: A complete urllib-parsed raw URL.

        Raises:
            VersionNotSupported: If the URL represents an OPTIMADE versioned base URL
                and the version part is not supported by the implementation.

        """
        base_url = get_base_url(url)
        optimade_path = f"{url.scheme}://{url.netloc}{url.path}"[len(base_url) :]
        match = re.match(r"^(?P<version>/v[0-9]+(\.[0-9]+){0,2}).*", optimade_path)
        if match is not None:
            if match.group("version") not in BASE_URL_PREFIXES.values():
                raise VersionNotSupported(
                    detail=(
                        f"The parsed versioned base URL {match.group('version')!r} from "
                        f"{url} is not supported by this implementation. "
                        f"Supported versioned base URLs are: {', '.join(BASE_URL_PREFIXES.values())}"
                    )
                )

    async def dispatch(self, request: Request, call_next):
        if request.url.path:
            self.check_url(request.url)
        response = await call_next(request)
        return response


class HandleApiHint(BaseHTTPMiddleware):
    """Handle `api_hint` query parameter."""

    @staticmethod
    def handle_api_hint(api_hint: List[str]) -> Union[None, str]:
        """Handle `api_hint` parameter value.

        There are several scenarios that can play out, when handling the `api_hint`
        query parameter:

        If several `api_hint` query parameters have been used, or a "standard" JSON
        list (`,`-separated value) has been supplied, a warning will be added to the
        response and the `api_hint` query parameter will not be applied.

        If the passed value does not comply with the rules set out in
        [the specification](https://github.com/Materials-Consortia/OPTIMADE/blob/v1.0.0/optimade.rst#version-negotiation),
        a warning will be added to the response and the `api_hint` query parameter
        will not be applied.

        If the value is part of the implementation's accepted versioned base URLs,
        it will be returned as is.

        If the value represents a major version that is newer than what is supported
        by the implementation, a `553 Version Not Supported` response will be returned,
        as is stated by [the specification](https://github.com/Materials-Consortia/OPTIMADE/blob/v1.0.0/optimade.rst#version-negotiation).

        On the other hand, if the value represents a major version equal to or lower
        than the implementation's supported major version, then the implementation's
        supported major version will be returned and tried for the request.

        Parameters:
            api_hint: The urllib-parsed query parameter value for `api_hint`.

        Raises:
            VersionNotSupported: If the requested major version is newer than the
                supported major version of the implementation.

        Returns:
            Either a valid `api_hint` value or `None`.

        """
        # Try to split by `,` if value is provided once, but in JSON-type "list" format
        _api_hint = []
        for value in api_hint:
            values = value.split(",")
            _api_hint.extend(values)
        api_hint = _api_hint

        if len(api_hint) > 1:
            warnings.warn(
                TooManyValues(
                    detail="`api_hint` should only be supplied once, with a single value."
                )
            )
            return None

        api_hint = f"/{api_hint[0]}"
        if re.match(r"^/v[0-9]+(\.[0-9]+)?$", api_hint) is None:
            warnings.warn(
                FieldValueNotRecognized(
                    detail=f"{api_hint[1:]!r} is not recognized as a valid `api_hint` value."
                )
            )
            return None

        if api_hint in BASE_URL_PREFIXES.values():
            return api_hint

        major_api_hint = int(re.findall(r"/v([0-9]+)", api_hint)[0])
        major_implementation = int(BASE_URL_PREFIXES["major"][len("/v") :])

        if major_api_hint > major_implementation:
            # Let's not try to handle a request for a newer major version
            raise VersionNotSupported(
                detail=(
                    f"The provided `api_hint` ({api_hint[1:]!r}) is not supported by this implementation. "
                    f"Supported versions include: {', '.join(BASE_URL_PREFIXES.values())}"
                )
            )
        if major_api_hint <= major_implementation:
            # If less than:
            # Use the current implementation in hope that it can still handle older requests
            #
            # If equal:
            # Go to /v<MAJOR>, since this should point to the latest available
            return BASE_URL_PREFIXES["major"]

    @staticmethod
    def is_versioned_base_url(url: str) -> bool:
        """Determine whether a request is for a versioned base URL.

        First, simply check whether a `/vMAJOR(.MINOR.PATCH)` part exists in the URL.
        If not, return `False`, else, remove unversioned base URL from the URL and check again.
        Return `bool` of final result.

        Parameters:
            url: The full URL to check.

        Returns:
            Whether or not the full URL represents an OPTIMADE versioned base URL.

        """
        if not re.findall(r"(/v[0-9]+(\.[0-9]+){0,2})", url):
            return False

        base_url = get_base_url(url)
        return bool(re.findall(r"(/v[0-9]+(\.[0-9]+){0,2})", url[len(base_url) :]))

    async def dispatch(self, request: Request, call_next):
        parsed_query = urllib.parse.parse_qs(request.url.query, keep_blank_values=True)

        if "api_hint" in parsed_query:
            if self.is_versioned_base_url(str(request.url)):
                warnings.warn(
                    QueryParamNotUsed(
                        detail=(
                            "`api_hint` provided with value{:s} '{:s}' for a versioned base URL. "
                            "In accordance with the specification, this will not be handled by "
                            "the implementation.".format(
                                "s" if len(parsed_query["api_hint"]) > 1 else "",
                                "', '".join(parsed_query["api_hint"]),
                            )
                        )
                    )
                )
            else:
                from optimade.server.routers.utils import get_base_url

                version_path = self.handle_api_hint(parsed_query["api_hint"])

                if version_path:
                    base_url = get_base_url(request.url)

                    new_request = (
                        f"{base_url}{version_path}{str(request.url)[len(base_url):]}"
                    )
                    url = urllib.parse.urlsplit(new_request)
                    parsed_query = urllib.parse.parse_qsl(
                        url.query, keep_blank_values=True
                    )
                    parsed_query = "&".join(
                        [
                            f"{key}={value}"
                            for key, value in parsed_query
                            if key != "api_hint"
                        ]
                    )
                    return RedirectResponse(
                        request.url.replace(path=url.path, query=parsed_query),
                        headers=request.headers,
                    )
                    # This is the non-URL changing solution:
                    #
                    # scope = request.scope
                    # scope["path"] = path
                    # request = Request(scope=scope, receive=request.receive, send=request._send)

        response = await call_next(request)
        return response


class AddWarnings(BaseHTTPMiddleware):
    """
    Add [`OptimadeWarning`][optimade.server.warnings.OptimadeWarning]s to the response.

    All sub-classes of [`OptimadeWarning`][optimade.server.warnings.OptimadeWarning]
    will also be added to the response's
    [`meta.warnings`][optimade.models.optimade_json.ResponseMeta.warnings] list.

    By overriding the `warnings.showwarning()` function with the
    [`showwarning` method][optimade.server.middleware.AddWarnings.showwarning],
    all usages of `warnings.warn()` will result in the regular printing of the
    warning message to `stderr`, but also its addition to an in-memory list of
    warnings.
    This middleware will, after the URL request has been handled, add the list of
    accumulated warnings to the JSON response under the
    [`meta.warnings`][optimade.models.optimade_json.ResponseMeta.warnings] field.

    To make sure the last part happens correctly and a Starlette `StreamingResponse`
    is returned, as is expected from a `BaseHTTPMiddleware` sub-class, one is
    instantiated with the updated `Content-Length` header, as well as making sure
    the response's body content is actually streamable, by breaking it down into
    chunks of the original response's chunk size.

    !!! warning "Important"
        It is **recommended** to add this middleware as the _last one_ to your application.

        This is to ensure it is invoked _first_, updating `warnings.showwarning()` and
        catching all warnings that should be added to the response.

        This can be achieved by applying `AddWarnings` _after_ all
        other middleware with the `.add_middleware()` method, or by
        initialising the app with a middleware list in which `AddWarnings`
        appears _first_. More information can be found in the docstring of
        [`OPTIMADE_MIDDLEWARE`][optimade.server.middleware.OPTIMADE_MIDDLEWARE].

    Attributes:
        _warnings (List[Warnings]): List of [`Warnings`][optimade.models.optimade_json.Warnings]
            added through usages of `warnings.warn()` via [`showwarning`][optimade.server.middleware.AddWarnings.showwarning].

    """

    def showwarning(
        self,
        message: Warning,
        category: Type[Warning],
        filename: str,
        lineno: int,
        file: Optional[IO] = None,
        line: Optional[str] = None,
    ) -> None:
        """
        Hook to write a warning to a file using the built-in `warnings` lib.

        In [the documentation](https://docs.python.org/3/library/warnings.html)
        for the built-in `warnings` library, there are a few recommended ways of
        customizing the printing of warning messages.

        This method can override the `warnings.showwarning` function,
        which is called as part of the `warnings` library's workflow to print
        warning messages, e.g., when using `warnings.warn()`.
        Originally, it prints warning messages to `stderr`.
        This method will also print warning messages to `stderr` by calling
        `warnings._showwarning_orig()` or `warnings._showwarnmsg_impl()`.
        The first function will be called if the issued warning is not recognized
        as an [`OptimadeWarning`][optimade.server.warnings.OptimadeWarning].
        This is equivalent to "standard behaviour".
        The second function will be called _after_ an
        [`OptimadeWarning`][optimade.server.warnings.OptimadeWarning] has been handled.

        An [`OptimadeWarning`][optimade.server.warnings.OptimadeWarning] will be
        translated into an OPTIMADE Warnings JSON object in accordance with
        [the specification](https://github.com/Materials-Consortia/OPTIMADE/blob/v1.0.0/optimade.rst#json-response-schema-common-fields).
        This process is similar to the [Exception handlers][optimade.server.exception_handlers].

        Parameters:
            message: The `Warning` object to show and possibly handle.
            category: `Warning` type being warned about. This amounts to `type(message)`.
            filename: Name of the file, where the warning was issued.
            lineno: Line number in the file, where the warning was issued.
            file: A file-like object to which the warning should be written.
            line: Source content of the line that issued the warning.

        """
        assert isinstance(
            message, Warning
        ), "'message' is expected to be a Warning or subclass thereof."

        if not isinstance(message, OptimadeWarning):
            # If the Warning is not an OptimadeWarning or subclass thereof,
            # use the regular 'showwarning' function.
            warnings._showwarning_orig(message, category, filename, lineno, file, line)
            return

        # Format warning
        try:
            title = str(message.title)
        except AttributeError:
            title = str(message.__class__.__name__)

        try:
            detail = str(message.detail)
        except AttributeError:
            detail = str(message)

        if CONFIG.debug:
            if line is None:
                # All this is taken directly from the warnings library.
                # See 'warnings._formatwarnmsg_impl()' for the original code.
                try:
                    import linecache

                    line = linecache.getline(filename, lineno)
                except Exception:
                    # When a warning is logged during Python shutdown, linecache
                    # and the import machinery don't work anymore
                    line = None
                    linecache = None
            meta = {
                "filename": filename,
                "lineno": lineno,
            }
            if line:
                meta["line"] = line.strip()

        if CONFIG.debug:
            new_warning = Warnings(title=title, detail=detail, meta=meta)
        else:
            new_warning = Warnings(title=title, detail=detail)

        # Add new warning to self._warnings
        self._warnings.append(new_warning.dict(exclude_unset=True))

        # Show warning message as normal in sys.stderr
        warnings._showwarnmsg_impl(
            warnings.WarningMessage(message, category, filename, lineno, file, line)
        )

    @staticmethod
    def chunk_it_up(content: str, chunk_size: int) -> Generator:
        """Return generator for string in chunks of size `chunk_size`.

        Parameters:
            content: String-content to separate into chunks.
            chunk_size: The size of the chunks, i.e. the length of the string-chunks.

        Returns:
            A Python generator to be converted later to an `asyncio` generator.

        """
        if chunk_size <= 0:
            chunk_size = 1
        return (content[i : chunk_size + i] for i in range(0, len(content), chunk_size))

    async def dispatch(self, request: Request, call_next):
        self._warnings = []

        warnings.simplefilter(action="default", category=OptimadeWarning)
        warnings.showwarning = self.showwarning

        response = await call_next(request)

        status = response.status_code
        headers = response.headers
        media_type = response.media_type
        background = response.background
        charset = response.charset

        body = b""
        first_run = True
        async for chunk in response.body_iterator:
            if first_run:
                first_run = False
                chunk_size = len(chunk)
            if not isinstance(chunk, bytes):
                chunk = chunk.encode(charset)
            body += chunk
        body = body.decode(charset)

        if self._warnings:
            response = json.loads(body)
            response.get("meta", {})["warnings"] = self._warnings
            body = json.dumps(response)
            if "content-length" in headers:
                headers["content-length"] = str(len(body))

        response = StreamingResponse(
            content=self.chunk_it_up(body, chunk_size),
            status_code=status,
            headers=headers,
            media_type=media_type,
            background=background,
        )

        return response


OPTIMADE_MIDDLEWARE: Tuple[BaseHTTPMiddleware] = (
    EnsureQueryParamIntegrity,
    CheckWronglyVersionedBaseUrls,
    HandleApiHint,
    AddWarnings,
)
"""A tuple of all the middleware classes that implement certain required
features of the OPTIMADE specification, e.g. warnings and URL
versioning.

!!! note
    The order in which middleware is added to an application matters.

    As discussed in the docstring of
    [`AddWarnings`][optimade.server.middleware.AddWarnings], this
    middleware is the final entry to this list so that it is the first
    to be applied by the server.
    Any other middleware should therefore be added _before_ iterating
    through this variable.
    This is the opposite way around to the example in the
    [Starlette documentation](https://www.starlette.io/middleware/)
    which initialises the application with a pre-built middleware list
    in the _reverse_ order to `OPTIMADE_MIDDLEWARE`.

To use this variable in FastAPI app code after initialisation:

```python
from fastapi import FastAPI
app = FastAPI()
for middleware in OPTIMADE_MIDDLEWARE:
    app.add_middleware(middleware)
```

Alternatively, to use this variable on initialisation:

```python
from fastapi import FastAPI
from starlette.middleware import Middleware
app = FastAPI(
    ...,
    middleware=[Middleware(m) for m in reversed(OPTIMADE_MIDDLEWARE)]
)
```

"""
