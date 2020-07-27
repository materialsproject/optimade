class OptimadeWarning(Warning):
    """Base Warning for the `optimade` package"""

    def __init__(
        self, detail: str = None, headers: dict = None, title: str = None, *args,
    ) -> None:
        super().__init__(detail, *args)
        self.detail = detail
        self.headers = headers
        self.title = title

    def __repr__(self) -> str:
        attrs = {
            "detail": repr(self.detail),
            "headers": repr(self.headers),
            "title": repr(self.title),
        }
        return "<{}({})>".format(
            self.__class__.__name__,
            " ".join(
                [
                    f"{attr}={value}"
                    for attr, value in attrs.items()
                    if value is not None
                ]
            ),
        )

    def __str__(self) -> str:
        return self.detail if self.detail is not None else ""