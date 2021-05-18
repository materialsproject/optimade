class OptimadeWarning(Warning):
    """Base Warning for the `optimade` package"""

    def __init__(self, detail: str = None, title: str = None, *args) -> None:
        detail = detail if detail else self.__doc__
        super().__init__(detail, *args)
        self.detail = detail
        self.title = title if title else self.__class__.__name__

    def __repr__(self) -> str:
        attrs = {
            "detail": self.detail,
            "title": self.title,
        }
        return "<{:s}({:s})>".format(
            self.__class__.__name__,
            " ".join(
                [
                    f"{attr}={value!r}"
                    for attr, value in attrs.items()
                    if value is not None
                ]
            ),
        )

    def __str__(self) -> str:
        return self.detail if self.detail is not None else ""


class FieldValueNotRecognized(OptimadeWarning):
    """A field or value used in the request is not recognised by this implementation."""


class TooManyValues(OptimadeWarning):
    """A field or query parameter has too many values to be handled by this implementation."""


class QueryParamNotUsed(OptimadeWarning):
    """A query parameter is not used in this request."""


class MissingExpectedField(OptimadeWarning):
    """A field was provided with a null value when a related field was provided
    with a value."""


class TimestampNotRFCCompliant(OptimadeWarning):
    """A timestamp has been used in a filter that contains microseconds and is thus not
    RFC 3339 compliant. This may cause undefined behaviour in the query results.

    """
