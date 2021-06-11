from fastapi import HTTPException

__all__ = (
    "BadRequest",
    "VersionNotSupported",
    "Forbidden",
    "NotFound",
    "UnprocessableEntity",
    "NotImplementedResponse",
    "POSSIBLE_ERRORS",
)


class StrReprMixin(HTTPException):
    """This mixin can be useful when testing requires a string
    representation of an exception that contains the HTTPException
    detail string, rather than the standard Python exception message.
    """

    def __str__(self):
        return self.detail if self.detail is not None else self.__repr__()


class BadRequest(StrReprMixin, HTTPException):
    """400 Bad Request"""

    status_code: int = 400
    title: str = "Bad Request"

    def __init__(
        self,
        detail: str = None,
        headers: dict = None,
    ) -> None:
        super().__init__(status_code=self.status_code, detail=detail, headers=headers)


class VersionNotSupported(StrReprMixin, HTTPException):
    """553 Version Not Supported"""

    status_code: int = 553
    title: str = "Version Not Supported"

    def __init__(
        self,
        detail: str = None,
        headers: dict = None,
    ) -> None:
        super().__init__(status_code=self.status_code, detail=detail, headers=headers)


class Forbidden(StrReprMixin, HTTPException):
    """403 Forbidden"""

    status_code: int = 403
    title: str = "Forbidden"

    def __init__(
        self,
        detail: str = None,
        headers: dict = None,
    ) -> None:
        super().__init__(status_code=self.status_code, detail=detail, headers=headers)


class NotFound(StrReprMixin, HTTPException):
    """404 Not Found"""

    status_code: int = 404
    title: str = "Not Found"

    def __init__(
        self,
        detail: str = None,
        headers: dict = None,
    ) -> None:
        super().__init__(status_code=self.status_code, detail=detail, headers=headers)


class UnprocessableEntity(StrReprMixin, HTTPException):
    """422 Unprocessable Entity"""

    status_code: int = 422
    title: str = "Unprocessable Entity"

    def __init__(
        self,
        detail: str = None,
        headers: dict = None,
    ) -> None:
        super().__init__(status_code=self.status_code, detail=detail, headers=headers)


class InternalServerError(StrReprMixin, HTTPException):
    """500 Internal Server Error"""

    status_code: int = 500
    title: str = "Internal Server Error"

    def __init__(
        self,
        detail: str = None,
        headers: dict = None,
    ) -> None:
        super().__init__(status_code=self.status_code, detail=detail, headers=headers)


class NotImplementedResponse(StrReprMixin, HTTPException):
    """501 Not Implemented"""

    status_code: int = 501
    title: str = "Not Implemented"

    def __init__(
        self,
        detail: str = None,
        headers: dict = None,
    ) -> None:
        super().__init__(status_code=self.status_code, detail=detail, headers=headers)


POSSIBLE_ERRORS = (
    BadRequest,
    Forbidden,
    NotFound,
    UnprocessableEntity,
    InternalServerError,
    NotImplementedResponse,
    VersionNotSupported,
)
