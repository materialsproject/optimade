from optimade.server.warnings import OptimadeWarning

__all__ = ("AdapterPackageNotFound", "ConversionWarning")


class AdapterPackageNotFound(OptimadeWarning):
    """The package for an adapter cannot be found."""


class ConversionWarning(OptimadeWarning):
    """A non-critical error/fallback/choice happened during conversion of an entry to format."""
