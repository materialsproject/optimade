__version__ = "0.14.1"
__api_version__ = "1.0.1"


import sys

if sys.version_info.minor == 6:
    # Python 3.6
    import warnings

    warnings.filterwarnings(
        action="once",
        message=r"v0\.14 of the `optimade` package.*",
        category=DeprecationWarning,
        append=False,
    )
    warnings.warn(
        "v0.14 of the `optimade` package will be the last to support Python 3.6. "
        "Please upgrade to Python 3.7+ to use v0.15 and later versions of `optimade`.",
        DeprecationWarning,
    )
