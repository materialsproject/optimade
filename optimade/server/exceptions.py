from fastapi import HTTPException

__all__ = (
    "BadRequest",
    "VersionNotSupported",
    "Forbidden",
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

    def __init__(
        self,
        status_code: int = 400,
        detail: str = None,
        headers: dict = None,
        title: str = "Bad Request",
    ) -> None:
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.title = title


class VersionNotSupported(StrReprMixin, HTTPException):
    """553 Version Not Supported"""

    def __init__(
        self,
        status_code: int = 553,
        detail: str = None,
        headers: dict = None,
        title: str = "Version Not Supported",
    ) -> None:
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.title = title


class Forbidden(StrReprMixin, HTTPException):
    """403 Forbidden"""

    def __init__(
        self,
        status_code: int = 403,
        detail: str = None,
        headers: dict = None,
        title: str = "Forbidden",
    ) -> None:
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.title = title
