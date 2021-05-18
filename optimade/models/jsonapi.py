"""This module should reproduce JSON API v1.0 https://jsonapi.org/format/1.0/"""
# pylint: disable=no-self-argument
from typing import Optional, Union, List, Dict, Any, Type
from datetime import datetime, timezone
from pydantic import (  # pylint: disable=no-name-in-module
    BaseModel,
    AnyUrl,
    parse_obj_as,
    root_validator,
)
from optimade.models.utils import StrictField


__all__ = (
    "Meta",
    "Link",
    "JsonApi",
    "ToplevelLinks",
    "ErrorLinks",
    "ErrorSource",
    "BaseResource",
    "RelationshipLinks",
    "Relationship",
    "Relationships",
    "ResourceLinks",
    "Attributes",
    "Resource",
    "Response",
)


class Meta(BaseModel):
    """Non-standard meta-information that can not be represented as an attribute or relationship."""

    class Config:
        extra = "allow"


class Link(BaseModel):
    """A link **MUST** be represented as either: a string containing the link's URL or a link object."""

    href: AnyUrl = StrictField(..., description="a string containing the link’s URL.")
    meta: Optional[Meta] = StrictField(
        None,
        description="a meta object containing non-standard meta-information about the link.",
    )


class JsonApi(BaseModel):
    """An object describing the server's implementation"""

    version: str = StrictField(
        default="1.0", description="Version of the json API used"
    )
    meta: Optional[Meta] = StrictField(
        None, description="Non-standard meta information"
    )


class ToplevelLinks(BaseModel):
    """A set of Links objects, possibly including pagination"""

    self: Optional[Union[AnyUrl, Link]] = StrictField(
        None, description="A link to itself"
    )
    related: Optional[Union[AnyUrl, Link]] = StrictField(
        None, description="A related resource link"
    )

    # Pagination
    first: Optional[Union[AnyUrl, Link]] = StrictField(
        None, description="The first page of data"
    )
    last: Optional[Union[AnyUrl, Link]] = StrictField(
        None, description="The last page of data"
    )
    prev: Optional[Union[AnyUrl, Link]] = StrictField(
        None, description="The previous page of data"
    )
    next: Optional[Union[AnyUrl, Link]] = StrictField(
        None, description="The next page of data"
    )

    @root_validator(pre=False)
    def check_additional_keys_are_links(cls, values):
        """The `ToplevelLinks` class allows any additional keys, as long as
        they are also Links or Urls themselves.

        """
        for key, value in values.items():
            if key not in cls.schema()["properties"]:
                values[key] = parse_obj_as(Optional[Union[AnyUrl, Link]], value)

        return values

    class Config:
        extra = "allow"


class ErrorLinks(BaseModel):
    """A Links object specific to Error objects"""

    about: Optional[Union[AnyUrl, Link]] = StrictField(
        None,
        description="A link that leads to further details about this particular occurrence of the problem.",
    )


class ErrorSource(BaseModel):
    """an object containing references to the source of the error"""

    pointer: Optional[str] = StrictField(
        None,
        description="a JSON Pointer [RFC6901] to the associated entity in the request document "
        '[e.g. "/data" for a primary data object, or "/data/attributes/title" for a specific attribute].',
    )
    parameter: Optional[str] = StrictField(
        None,
        description="a string indicating which URI query parameter caused the error.",
    )


class Error(BaseModel):
    """An error response"""

    id: Optional[str] = StrictField(
        None,
        description="A unique identifier for this particular occurrence of the problem.",
    )
    links: Optional[ErrorLinks] = StrictField(
        None, description="A links object storing about"
    )
    status: Optional[str] = StrictField(
        None,
        description="the HTTP status code applicable to this problem, expressed as a string value.",
    )
    code: Optional[str] = StrictField(
        None,
        description="an application-specific error code, expressed as a string value.",
    )
    title: Optional[str] = StrictField(
        None,
        description="A short, human-readable summary of the problem. "
        "It **SHOULD NOT** change from occurrence to occurrence of the problem, except for purposes of localization.",
    )
    detail: Optional[str] = StrictField(
        None,
        description="A human-readable explanation specific to this occurrence of the problem.",
    )
    source: Optional[ErrorSource] = StrictField(
        None, description="An object containing references to the source of the error"
    )
    meta: Optional[Meta] = StrictField(
        None,
        description="a meta object containing non-standard meta-information about the error.",
    )

    def __hash__(self):
        return hash(self.json())


class BaseResource(BaseModel):
    """Minimum requirements to represent a Resource"""

    id: str = StrictField(..., description="Resource ID")
    type: str = StrictField(..., description="Resource type")

    class Config:
        @staticmethod
        def schema_extra(schema: Dict[str, Any], model: Type["BaseResource"]) -> None:
            """Ensure `id` and `type` are the first two entries in the list required properties.

            Note:
                This _requires_ that `id` and `type` are the _first_ model fields defined
                for all sub-models of `BaseResource`.

            """
            if "id" not in schema.get("required", []):
                schema["required"] = ["id"] + schema.get("required", [])
            if "type" not in schema.get("required", []):
                required = []
                for field in schema.get("required", []):
                    required.append(field)
                    if field == "id":
                        # To make sure the property order match the listed properties,
                        # this ensures "type" is added immediately after "id".
                        required.append("type")
                schema["required"] = required


class RelationshipLinks(BaseModel):
    """A resource object **MAY** contain references to other resource objects ("relationships").
    Relationships may be to-one or to-many.
    Relationships can be specified by including a member in a resource's links object.

    """

    self: Optional[Union[AnyUrl, Link]] = StrictField(
        None,
        description="""A link for the relationship itself (a 'relationship link').
This link allows the client to directly manipulate the relationship.
When fetched successfully, this link returns the [linkage](https://jsonapi.org/format/1.0/#document-resource-object-linkage) for the related resources as its primary data.
(See [Fetching Relationships](https://jsonapi.org/format/1.0/#fetching-relationships).)""",
    )
    related: Optional[Union[AnyUrl, Link]] = StrictField(
        None,
        description="A [related resource link](https://jsonapi.org/format/1.0/#document-resource-object-related-resource-links).",
    )

    @root_validator(pre=True)
    def either_self_or_related_must_be_specified(cls, values):
        for value in values.values():
            if value is not None:
                break
        else:
            raise ValueError(
                "Either 'self' or 'related' MUST be specified for RelationshipLinks"
            )
        return values


class Relationship(BaseModel):
    """Representation references from the resource object in which it’s defined to other resource objects."""

    links: Optional[RelationshipLinks] = StrictField(
        None,
        description="a links object containing at least one of the following: self, related",
    )
    data: Optional[Union[BaseResource, List[BaseResource]]] = StrictField(
        None, description="Resource linkage"
    )
    meta: Optional[Meta] = StrictField(
        None,
        description="a meta object that contains non-standard meta-information about the relationship.",
    )

    @root_validator(pre=True)
    def at_least_one_relationship_key_must_be_set(cls, values):
        for value in values.values():
            if value is not None:
                break
        else:
            raise ValueError(
                "Either 'links', 'data', or 'meta' MUST be specified for Relationship"
            )
        return values


class Relationships(BaseModel):
    """
    Members of the relationships object (\"relationships\") represent references from the resource object in which it's defined to other resource objects.
    Keys MUST NOT be:
        type
        id
    """

    @root_validator(pre=True)
    def check_illegal_relationships_fields(cls, values):
        illegal_fields = ("id", "type")
        for field in illegal_fields:
            if field in values:
                raise ValueError(
                    f"{illegal_fields} MUST NOT be fields under Relationships"
                )
        return values


class ResourceLinks(BaseModel):
    """A Resource Links object"""

    self: Optional[Union[AnyUrl, Link]] = StrictField(
        None,
        description="A link that identifies the resource represented by the resource object.",
    )


class Attributes(BaseModel):
    """
    Members of the attributes object ("attributes\") represent information about the resource object in which it's defined.
    The keys for Attributes MUST NOT be:
        relationships
        links
        id
        type
    """

    class Config:
        extra = "allow"

    @root_validator(pre=True)
    def check_illegal_attributes_fields(cls, values):
        illegal_fields = ("relationships", "links", "id", "type")
        for field in illegal_fields:
            if field in values:
                raise ValueError(
                    f"{illegal_fields} MUST NOT be fields under Attributes"
                )
        return values


class Resource(BaseResource):
    """Resource objects appear in a JSON API document to represent resources."""

    links: Optional[ResourceLinks] = StrictField(
        None, description="a links object containing links related to the resource."
    )
    meta: Optional[Meta] = StrictField(
        None,
        description="a meta object containing non-standard meta-information about a resource that can not be represented as an attribute or relationship.",
    )
    attributes: Optional[Attributes] = StrictField(
        None,
        description="an attributes object representing some of the resource’s data.",
    )
    relationships: Optional[Relationships] = StrictField(
        None,
        description="""[Relationships object](https://jsonapi.org/format/1.0/#document-resource-object-relationships)
describing relationships between the resource and other JSON API resources.""",
    )


class Response(BaseModel):
    """A top-level response"""

    data: Optional[Union[None, Resource, List[Resource]]] = StrictField(
        None, description="Outputted Data", uniqueItems=True
    )
    meta: Optional[Meta] = StrictField(
        None,
        description="A meta object containing non-standard information related to the Success",
    )
    errors: Optional[List[Error]] = StrictField(
        None, description="A list of unique errors", uniqueItems=True
    )
    included: Optional[List[Resource]] = StrictField(
        None, description="A list of unique included resources", uniqueItems=True
    )
    links: Optional[ToplevelLinks] = StrictField(
        None, description="Links associated with the primary data or errors"
    )
    jsonapi: Optional[JsonApi] = StrictField(
        None, description="Information about the JSON API used"
    )

    @root_validator(pre=True)
    def either_data_meta_or_errors_must_be_set(cls, values):
        required_fields = ("data", "meta", "errors")
        if not any(values.get(field) for field in required_fields):
            raise ValueError(
                f"At least one of {required_fields} MUST be specified in the top-level response"
            )
        return values

    class Config:
        """The specification mandates that datetimes must be encoded following
        [RFC3339](https://tools.ietf.org/html/rfc3339), which does not support
        fractional seconds, thus they must be stripped in the response. This can
        cause issues when the underlying database contains fields that do include
        microseconds, as filters may return unexpected results.
        """

        json_encoders = {
            datetime: lambda v: v.astimezone(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
        }
