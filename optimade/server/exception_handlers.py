import traceback
from typing import List, Tuple, Callable

from lark.exceptions import VisitError

from pydantic import ValidationError
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError, StarletteHTTPException
from fastapi import Request
from fastapi.responses import JSONResponse

from optimade.models import OptimadeError, ErrorResponse, ErrorSource

from optimade.server.config import CONFIG
from optimade.server.exceptions import BadRequest
from optimade.server.logger import LOGGER
from optimade.server.routers.utils import meta_values


def general_exception(
    request: Request,
    exc: Exception,
    status_code: int = 500,  # A status_code in `exc` will take precedence
    errors: List[OptimadeError] = None,
) -> JSONResponse:
    """Handle an exception

    Parameters:
        request: The HTTP request resulting in the exception being raised.
        exc: The exception being raised.
        status_code: The returned HTTP status code for the error response.
        errors: List of error resources as defined in
            [the OPTIMADE specification](https://github.com/Materials-Consortia/OPTIMADE/blob/develop/optimade.rst#json-response-schema-common-fields).

    Returns:
        A JSON HTTP response based on [`ErrorResponse`][optimade.models.responses.ErrorResponse].

    """
    debug_info = {}
    if CONFIG.debug:
        tb = "".join(
            traceback.format_exception(etype=type(exc), value=exc, tb=exc.__traceback__)
        )
        LOGGER.error("Traceback:\n%s", tb)
        debug_info[f"_{CONFIG.provider.prefix}_traceback"] = tb

    try:
        http_response_code = int(exc.status_code)
    except AttributeError:
        http_response_code = int(status_code)

    try:
        title = str(exc.title)
    except AttributeError:
        title = str(exc.__class__.__name__)

    try:
        detail = str(exc.detail)
    except AttributeError:
        detail = str(exc)

    if errors is None:
        errors = [OptimadeError(detail=detail, status=http_response_code, title=title)]

    response = ErrorResponse(
        meta=meta_values(
            url=request.url,
            data_returned=0,
            data_available=0,
            more_data_available=False,
            **debug_info,
        ),
        errors=errors,
    )

    return JSONResponse(
        status_code=http_response_code,
        content=jsonable_encoder(response, exclude_unset=True),
    )


def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Handle a general HTTP Exception from Starlette

    Parameters:
        request: The HTTP request resulting in the exception being raised.
        exc: The exception being raised.

    Returns:
        A JSON HTTP response through [`general_exception()`][optimade.server.exception_handlers.general_exception].

    """
    return general_exception(request, exc)


def request_validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle a request validation error from FastAPI

    `RequestValidationError` is a specialization of a general pydantic `ValidationError`.
    Pass-through directly to [`general_exception()`][optimade.server.exception_handlers.general_exception].

    Parameters:
        request: The HTTP request resulting in the exception being raised.
        exc: The exception being raised.

    Returns:
        A JSON HTTP response through [`general_exception()`][optimade.server.exception_handlers.general_exception].

    """
    return general_exception(request, exc)


def validation_exception_handler(
    request: Request, exc: ValidationError
) -> JSONResponse:
    """Handle a general pydantic validation error

    The pydantic `ValidationError` usually contains a list of errors,
    this function extracts them and wraps them in the OPTIMADE specific error resource.

    Parameters:
        request: The HTTP request resulting in the exception being raised.
        exc: The exception being raised.

    Returns:
        A JSON HTTP response through [`general_exception()`][optimade.server.exception_handlers.general_exception].

    """
    status = 500
    title = "ValidationError"
    errors = set()
    for error in exc.errors():
        pointer = "/" + "/".join([str(_) for _ in error["loc"]])
        source = ErrorSource(pointer=pointer)
        code = error["type"]
        detail = error["msg"]
        errors.add(
            OptimadeError(
                detail=detail, status=status, title=title, source=source, code=code
            )
        )
    return general_exception(request, exc, status_code=status, errors=list(errors))


def grammar_not_implemented_handler(request: Request, exc: VisitError) -> JSONResponse:
    """Handle an error raised by Lark during filter transformation

    All errors raised during filter transformation are wrapped in the Lark `VisitError`.
    According to the OPTIMADE specification, these errors are repurposed to be 501 NotImplementedErrors.

    For special exceptions, like [`BadRequest`][optimade.server.exceptions.BadRequest], we pass-through to
    [`general_exception()`][optimade.server.exception_handlers.general_exception], since they should not
    return a 501 NotImplementedError.

    Parameters:
        request: The HTTP request resulting in the exception being raised.
        exc: The exception being raised.

    Returns:
        A JSON HTTP response through [`general_exception()`][optimade.server.exception_handlers.general_exception].

    """
    pass_through_exceptions = (BadRequest,)

    orig_exc = getattr(exc, "orig_exc", None)
    if isinstance(orig_exc, pass_through_exceptions):
        return general_exception(request, orig_exc)

    rule = getattr(exc.obj, "data", getattr(exc.obj, "type", str(exc)))

    status = 501
    title = "NotImplementedError"
    detail = (
        f"Error trying to process rule '{rule}'"
        if not str(exc.orig_exc)
        else str(exc.orig_exc)
    )
    error = OptimadeError(detail=detail, status=status, title=title)
    return general_exception(request, exc, status_code=status, errors=[error])


def not_implemented_handler(request: Request, exc: NotImplementedError) -> JSONResponse:
    """Handle a standard NotImplementedError Python exception

    Parameters:
        request: The HTTP request resulting in the exception being raised.
        exc: The exception being raised.

    Returns:
        A JSON HTTP response through [`general_exception()`][optimade.server.exception_handlers.general_exception].

    """
    status = 501
    title = "NotImplementedError"
    detail = str(exc)
    error = OptimadeError(detail=detail, status=status, title=title)
    return general_exception(request, exc, status_code=status, errors=[error])


def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch all Python Exceptions not handled by other exception handlers

    Pass-through directly to [`general_exception()`][optimade.server.exception_handlers.general_exception].

    Parameters:
        request: The HTTP request resulting in the exception being raised.
        exc: The exception being raised.

    Returns:
        A JSON HTTP response through [`general_exception()`][optimade.server.exception_handlers.general_exception].

    """
    return general_exception(request, exc)


OPTIMADE_EXCEPTIONS: Tuple[Exception, Callable[[Request, Exception], JSONResponse]] = (
    (StarletteHTTPException, http_exception_handler),
    (RequestValidationError, request_validation_exception_handler),
    (ValidationError, validation_exception_handler),
    (VisitError, grammar_not_implemented_handler),
    (NotImplementedError, not_implemented_handler),
    (Exception, general_exception_handler),
)
"""A tuple of all pairs of exceptions and handler functions that allow for
appropriate responses to be returned in certain scenarios according to the
OPTIMADE specification.

To use these in FastAPI app code:

```python
from fastapi import FastAPI
app = FastAPI()
for exception, handler in OPTIMADE_EXCEPTIONS:
    app.add_exception_handler(exception, handler)
```

"""
