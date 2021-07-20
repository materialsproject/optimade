"""This submodule implements the [`LarkParser`][optimade.filterparser.LarkParser] class,
which uses the lark library to parse filter strings with a defined OPTIMADE filter grammar
into `Lark.Tree` objects for use by the filter transformers.

"""

from pathlib import Path
from typing import Dict, Tuple
from collections import defaultdict

from lark import Lark, Tree

from optimade.server.exceptions import BadRequest

__all__ = ("ParserError", "LarkParser")


class ParserError(Exception):
    """Triggered by critical parsing errors that should lead
    to 500 Server Error HTTP statuses.
    """


def get_versions() -> Dict[Tuple[int, int, int], Dict[str, str]]:
    """Find grammar files within this package's grammar directory,
    returning a dictionary broken down by scraped grammar version
    (major, minor, patch) and variant (a string tag).

    Returns:
        A mapping from version, variant to grammar file name.

    """
    dct = defaultdict(dict)
    for filename in Path(__file__).parent.joinpath("../grammar").glob("*.lark"):
        tags = filename.stem.lstrip("v").split(".")
        version = tuple(map(int, tags[:3]))
        variant = "default" if len(tags) == 3 else tags[-1]
        dct[version][variant] = filename
    return dict(dct)


AVAILABLE_PARSERS = get_versions()


class LarkParser:
    """This class wraps a versioned OPTIMADE grammar and allows
    it to be parsed into Lark tree objects.

    """

    def __init__(self, version: Tuple[int, int, int] = None, variant: str = "default"):
        """For a given version and variant, try to load the corresponding grammar.

        Parameters:
            version: The grammar version number to use (e.g., `(1, 0, 1)` for v1.0.1).
            variant: The grammar variant to employ.

        Raises:
            ParserError: If the requested version/variant of the
                grammar does not exist.

        """

        if not version:
            version = max(
                v for v in AVAILABLE_PARSERS if AVAILABLE_PARSERS[v].get("default")
            )

        if version not in AVAILABLE_PARSERS:
            raise ParserError(f"Unknown parser grammar version: {version}")

        if variant not in AVAILABLE_PARSERS[version]:
            raise ParserError(f"Unknown variant of the parser: {variant}")

        self.version = version
        self.variant = variant

        with open(AVAILABLE_PARSERS[version][variant]) as f:
            self.lark = Lark(f)

        self.tree = None
        self.filter = None

    def parse(self, filter_: str) -> Tree:
        """Parse a filter string into a `lark.Tree`.

        Parameters:
            filter_: The filter string to parse.

        Raises:
            BadRequest: If the filter cannot be parsed.

        Returns:
            The parsed filter.

        """
        try:
            self.tree = self.lark.parse(filter_)
            self.filter = filter_
            return self.tree
        except Exception as exc:
            raise BadRequest(
                detail=f"Unable to parse filter {filter_}. Lark traceback: \n{exc}"
            ) from exc

    def __repr__(self):
        if isinstance(self.tree, Tree):
            return self.tree.pretty()
        return repr(self.lark)
