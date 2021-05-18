# pylint: disable=line-too-long,no-self-argument
from datetime import datetime
from typing import Optional, Dict, List
from pydantic import BaseModel, Field, validator  # pylint: disable=no-name-in-module

from optimade.models.jsonapi import Relationships, Attributes, Resource
from optimade.models.optimade_json import Relationship, DataType
from optimade.models.utils import StrictField, OptimadeField, SupportLevel


__all__ = (
    "EntryRelationships",
    "EntryResourceAttributes",
    "EntryResource",
    "EntryInfoProperty",
    "EntryInfoResource",
)


class TypedRelationship(Relationship):
    # This may be updated when moving to Python 3.8
    @validator("data")
    def check_rel_type(cls, data):
        if not isinstance(data, list):
            # All relationships at this point are empty-to-many relationships in JSON:API:
            # https://jsonapi.org/format/1.0/#document-resource-object-linkage
            raise ValueError("`data` key in a relationship must always store a list.")
        if hasattr(cls, "_req_type") and any(
            getattr(obj, "type", None) != cls._req_type for obj in data
        ):
            raise ValueError("Object stored in relationship data has wrong type")
        return data


class ReferenceRelationship(TypedRelationship):
    _req_type = "references"


class StructureRelationship(TypedRelationship):
    _req_type = "structures"


class EntryRelationships(Relationships):
    """This model wraps the JSON API Relationships to include type-specific top level keys."""

    references: Optional[ReferenceRelationship] = StrictField(
        None,
        description="Object containing links to relationships with entries of the `references` type.",
    )

    structures: Optional[StructureRelationship] = StrictField(
        None,
        description="Object containing links to relationships with entries of the `structures` type.",
    )


class EntryResourceAttributes(Attributes):
    """Contains key-value pairs representing the entry's properties."""

    immutable_id: Optional[str] = OptimadeField(
        None,
        description="""The entry's immutable ID (e.g., an UUID). This is important for databases having preferred IDs that point to "the latest version" of a record, but still offer access to older variants. This ID maps to the version-specific record, in case it changes in the future.

- **Type**: string.

- **Requirements/Conventions**:
    - **Support**: OPTIONAL support in implementations, i.e., MAY be `null`.
    - **Query**: MUST be a queryable property with support for all mandatory filter features.

- **Examples**:
    - `"8bd3e750-b477-41a0-9b11-3a799f21b44f"`
    - `"fjeiwoj,54;@=%<>#32"` (Strings that are not URL-safe are allowed.)""",
        support=SupportLevel.OPTIONAL,
        queryable=SupportLevel.MUST,
    )

    last_modified: Optional[datetime] = OptimadeField(
        ...,
        description="""Date and time representing when the entry was last modified.

- **Type**: timestamp.

- **Requirements/Conventions**:
    - **Support**: SHOULD be supported by all implementations, i.e., SHOULD NOT be `null`.
    - **Query**: MUST be a queryable property with support for all mandatory filter features.
    - **Response**: REQUIRED in the response unless the query parameter `response_fields` is present and does not include this property.

- **Example**:
    - As part of JSON response format: `"2007-04-05T14:30:20Z"` (i.e., encoded as an [RFC 3339 Internet Date/Time Format](https://tools.ietf.org/html/rfc3339#section-5.6) string.)""",
        support=SupportLevel.SHOULD,
        queryable=SupportLevel.MUST,
    )


class EntryResource(Resource):
    """The base model for an entry resource."""

    id: str = OptimadeField(
        ...,
        description="""An entry's ID as defined in section Definition of Terms.

- **Type**: string.

- **Requirements/Conventions**:
    - **Support**: MUST be supported by all implementations, MUST NOT be `null`.
    - **Query**: MUST be a queryable property with support for all mandatory filter features.
    - **Response**: REQUIRED in the response.

- **Examples**:
    - `"db/1234567"`
    - `"cod/2000000"`
    - `"cod/2000000@1234567"`
    - `"nomad/L1234567890"`
    - `"42"`""",
        support=SupportLevel.MUST,
        queryable=SupportLevel.MUST,
    )

    type: str = Field(
        description="""The name of the type of an entry.

- **Type**: string.

- **Requirements/Conventions**:
    - **Support**: MUST be supported by all implementations, MUST NOT be `null`.
    - **Query**: MUST be a queryable property with support for all mandatory filter features.
    - **Response**: REQUIRED in the response.
    - MUST be an existing entry type.
    - The entry of type `<type>` and ID `<id>` MUST be returned in response to a request for `/<type>/<id>` under the versioned base URL.

- **Example**: `"structures"`""",
        support=SupportLevel.MUST,
        queryable=SupportLevel.MUST,
    )

    attributes: EntryResourceAttributes = StrictField(
        ...,
        description="""A dictionary, containing key-value pairs representing the entry's properties, except for `type` and `id`.
Database-provider-specific properties need to include the database-provider-specific prefix (see section on Database-Provider-Specific Namespace Prefixes).""",
    )

    relationships: Optional[EntryRelationships] = StrictField(
        None,
        description="""A dictionary containing references to other entries according to the description in section Relationships encoded as [JSON API Relationships](https://jsonapi.org/format/1.0/#document-resource-object-relationships).
The OPTIONAL human-readable description of the relationship MAY be provided in the `description` field inside the `meta` dictionary of the JSON API resource identifier object.""",
    )


class EntryInfoProperty(BaseModel):

    description: str = StrictField(
        ..., description="A human-readable description of the entry property"
    )

    unit: Optional[str] = StrictField(
        None,
        description="""The physical unit of the entry property.
This MUST be a valid representation of units according to version 2.1 of [The Unified Code for Units of Measure](https://unitsofmeasure.org/ucum.html).
It is RECOMMENDED that non-standard (non-SI) units are described in the description for the property.""",
    )

    sortable: Optional[bool] = StrictField(
        None,
        description="""Defines whether the entry property can be used for sorting with the "sort" parameter.
If the entry listing endpoint supports sorting, this key MUST be present for sortable properties with value `true`.""",
    )

    type: Optional[DataType] = StrictField(
        None,
        title="Type",
        description="""The type of the property's value.
This MUST be any of the types defined in the Data types section.
For the purpose of compatibility with future versions of this specification, a client MUST accept values that are not `string` values specifying any of the OPTIMADE Data types, but MUST then also disregard the `type` field.
Note, if the value is a nested type, only the outermost type should be reported.
E.g., for the entry resource `structures`, the `species` property is defined as a list of dictionaries, hence its `type` value would be `list`.""",
    )


class EntryInfoResource(BaseModel):

    formats: List[str] = StrictField(
        ..., description="List of output formats available for this type of entry."
    )

    description: str = StrictField(..., description="Description of the entry.")

    properties: Dict[str, EntryInfoProperty] = StrictField(
        ...,
        description="A dictionary describing queryable properties for this entry type, where each key is a property name.",
    )

    output_fields_by_format: Dict[str, List[str]] = StrictField(
        ...,
        description="Dictionary of available output fields for this entry type, where the keys are the values of the `formats` list and the values are the keys of the `properties` dictionary.",
    )
