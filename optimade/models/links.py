# pylint: disable=no-self-argument
from enum import Enum

from pydantic import (  # pylint: disable=no-name-in-module
    AnyUrl,
    root_validator,
)
from typing import Union, Optional

from optimade.models.jsonapi import Link, Attributes
from optimade.models.entries import EntryResource
from optimade.models.utils import StrictField


__all__ = (
    "LinksResourceAttributes",
    "LinksResource",
)


class LinkType(Enum):
    """Enumeration of link_type values"""

    CHILD = "child"
    ROOT = "root"
    EXTERNAL = "external"
    PROVIDERS = "providers"


class Aggregate(Enum):
    """Enumeration of aggregate values"""

    OK = "ok"
    TEST = "test"
    STAGING = "staging"
    NO = "no"


class LinksResourceAttributes(Attributes):
    """Links endpoint resource object attributes"""

    name: str = StrictField(
        ...,
        description="Human-readable name for the OPTIMADE API implementation, e.g., for use in clients to show the name to the end-user.",
    )
    description: str = StrictField(
        ...,
        description="Human-readable description for the OPTIMADE API implementation, e.g., for use in clients to show a description to the end-user.",
    )
    base_url: Optional[Union[AnyUrl, Link]] = StrictField(
        ...,
        description="JSON API links object, pointing to the base URL for this implementation",
    )

    homepage: Optional[Union[AnyUrl, Link]] = StrictField(
        ...,
        description="JSON API links object, pointing to a homepage URL for this implementation",
    )

    link_type: LinkType = StrictField(
        ...,
        title="Link Type",
        description="""The type of the linked relation.
MUST be one of these values: 'child', 'root', 'external', 'providers'.""",
    )

    aggregate: Optional[Aggregate] = StrictField(
        Aggregate.OK,
        title="Aggregate",
        description="""A string indicating whether a client that is following links to aggregate results from different OPTIMADE implementations should follow this link or not.
This flag SHOULD NOT be indicated for links where `link_type` is not `child`.

If not specified, clients MAY assume that the value is `ok`.
If specified, and the value is anything different than `ok`, the client MUST assume that the server is suggesting not to follow the link during aggregation by default (also if the value is not among the known ones, in case a future specification adds new accepted values).

Specific values indicate the reason why the server is providing the suggestion.
A client MAY follow the link anyway if it has reason to do so (e.g., if the client is looking for all test databases, it MAY follow the links marked with `aggregate`=`test`).

If specified, it MUST be one of the values listed in section Link Aggregate Options.""",
    )

    no_aggregate_reason: Optional[str] = StrictField(
        None,
        description="""An OPTIONAL human-readable string indicating the reason for suggesting not to aggregate results following the link.
It SHOULD NOT be present if `aggregate`=`ok`.""",
    )


class LinksResource(EntryResource):
    """A Links endpoint resource object"""

    type: str = StrictField(
        "links",
        const="links",
        description="These objects are described in detail in the section Links Endpoint",
        pattern="^links$",
    )

    attributes: LinksResourceAttributes = StrictField(
        ...,
        description="A dictionary containing key-value pairs representing the Links resource's properties.",
    )

    @root_validator(pre=True)
    def relationships_must_not_be_present(cls, values):
        if values.get("relationships", None) is not None:
            raise ValueError('"relationships" is not allowed for links resources')
        return values
