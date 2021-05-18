from abc import abstractmethod, ABC
from typing import Tuple, List, Union, Dict, Any
import warnings
import re

from lark import Transformer
from fastapi import HTTPException

from optimade.filterparser import LarkParser
from optimade.models import EntryResource
from optimade.server.config import CONFIG, SupportedBackend
from optimade.server.exceptions import BadRequest, Forbidden
from optimade.server.mappers import BaseResourceMapper
from optimade.server.query_params import EntryListingQueryParams, SingleEntryQueryParams
from optimade.server.warnings import FieldValueNotRecognized, UnknownProviderProperty


def create_collection(
    name: str, resource_cls: EntryResource, resource_mapper: BaseResourceMapper
) -> "EntryCollection":
    """Create an `EntryCollection` of the configured type, depending on the value of
    `CONFIG.database_backend`.

    Arguments:
        name: The collection name.
        resource_cls: The type of entry resource to be stored within the collection.
        resource_mapper: The associated resource mapper for that entry resource type.

    Returns:
        The created `EntryCollection`.

    """
    if CONFIG.database_backend in (
        SupportedBackend.MONGODB,
        SupportedBackend.MONGOMOCK,
    ):
        from optimade.server.entry_collections.mongo import MongoCollection

        return MongoCollection(
            name=name,
            resource_cls=resource_cls,
            resource_mapper=resource_mapper,
        )

    if CONFIG.database_backend is SupportedBackend.ELASTIC:
        from optimade.server.entry_collections.elasticsearch import ElasticCollection

        return ElasticCollection(
            name=name,
            resource_cls=resource_cls,
            resource_mapper=resource_mapper,
        )

    raise NotImplementedError(
        f"The database backend {CONFIG.database_backend!r} is not implemented"
    )


class EntryCollection(ABC):
    """Backend-agnostic base class for querying collections of
    [`EntryResource`][optimade.models.entries.EntryResource]s."""

    def __init__(
        self,
        resource_cls: EntryResource,
        resource_mapper: BaseResourceMapper,
        transformer: Transformer,
    ):
        """Initialize the collection for the given parameters.

        Parameters:
            resource_cls (EntryResource): The `EntryResource` model
                that is stored by the collection.
            resource_mapper (BaseResourceMapper): A resource mapper
                object that handles aliases and format changes between
                deserialization and response.
            transformer (Transformer): The Lark `Transformer` used to
                interpret the filter.

        """
        self.parser = LarkParser()
        self.resource_cls = resource_cls
        self.resource_mapper = resource_mapper
        self.transformer = transformer

        self.provider_prefix = CONFIG.provider.prefix
        self.provider_fields = CONFIG.provider_fields.get(resource_mapper.ENDPOINT, [])

    @abstractmethod
    def __len__(self) -> int:
        """Returns the total number of entries in the collection."""

    @abstractmethod
    def insert(self, data: List[EntryResource]) -> None:
        """Add the given entries to the underlying database.

        Arguments:
            data: The entry resource objects to add to the database.

        """

    @abstractmethod
    def count(self, **kwargs) -> int:
        """Returns the number of entries matching the query specified
        by the keyword arguments.

        Parameters:
            kwargs (dict): Query parameters as keyword arguments.

        """

    def find(
        self, params: EntryListingQueryParams
    ) -> Tuple[List[EntryResource], int, bool, set]:
        """
        Fetches results and indicates if more data is available.

        Also gives the total number of data available in the absence of `page_limit`.
        See [`EntryListingQueryParams`][optimade.server.query_params.EntryListingQueryParams]
        for more information.

        Parameters:
            params (EntryListingQueryParams): entry listing URL query params

        Returns:
            (`results`, `data_returned`, `more_data_available`, `fields`).

        """
        criteria = self.handle_query_params(params)
        single_entry = isinstance(params, SingleEntryQueryParams)
        response_fields = criteria.pop("fields")

        results, data_returned, more_data_available = self._run_db_query(
            criteria, single_entry=isinstance(params, SingleEntryQueryParams)
        )

        if single_entry:
            results = results[0] if results else None

            if data_returned > 1:
                raise HTTPException(
                    status_code=404,
                    detail=f"Instead of a single entry, {data_returned} entries were found",
                )

        exclude_fields = self.all_fields - response_fields
        include_fields = (
            response_fields - self.resource_mapper.TOP_LEVEL_NON_ATTRIBUTES_FIELDS
        )

        bad_optimade_fields = set()
        bad_provider_fields = set()
        for field in include_fields:
            if field not in self.resource_mapper.ALL_ATTRIBUTES:
                if field.startswith("_"):
                    if any(
                        field.startswith(f"_{prefix}_")
                        for prefix in self.resource_mapper.SUPPORTED_PREFIXES
                    ):
                        bad_provider_fields.add(field)
                else:
                    bad_optimade_fields.add(field)

        if bad_provider_fields:
            warnings.warn(
                message=f"Unrecognised field(s) for this provider requested in `response_fields`: {bad_provider_fields}.",
                category=UnknownProviderProperty,
            )

        if bad_optimade_fields:
            raise BadRequest(
                detail=f"Unrecognised OPTIMADE field(s) in requested `response_fields`: {bad_optimade_fields}."
            )

        if results:
            if isinstance(results, dict):
                results = self.resource_cls(**self.resource_mapper.map_back(results))
            else:
                results = [
                    self.resource_cls(**self.resource_mapper.map_back(doc))
                    for doc in results
                ]

        return (
            results,
            data_returned,
            more_data_available,
            exclude_fields,
            include_fields,
        )

    @abstractmethod
    def _run_db_query(
        self, criteria: Dict[str, Any], single_entry: bool = False
    ) -> Tuple[List[Dict[str, Any]], int, bool]:
        """Run the query on the backend and collect the results.

        Arguments:
            criteria: A dictionary representation of the query parameters.
            single_entry: Whether or not the caller is expecting a single entry response.

        Returns:
            The list of entries from the database (without any re-mapping), the total number of
            entries matching the query and a boolean for whether or not there is more data available.

        """

    @property
    def all_fields(self) -> set:
        """Get the set of all fields handled in this collection,
        from attribute fields in the schema, provider fields and top-level OPTIMADE fields.

        Returns:
            All fields handled in this collection.

        """
        # All OPTIMADE fields
        fields = self.resource_mapper.TOP_LEVEL_NON_ATTRIBUTES_FIELDS.copy()
        fields |= self.get_attribute_fields()
        # All provider-specific fields
        fields |= {
            f"_{self.provider_prefix}_{field_name}"
            for field_name in self.provider_fields
        }

        return fields

    def get_attribute_fields(self) -> set:
        """Get the set of attribute fields

        Return only the _first-level_ attribute fields from the schema of the resource class,
        resolving references along the way if needed.

        Note:
            It is not needed to take care of other special OpenAPI schema keys than `allOf`,
            since only `allOf` will be found in this context.
            Other special keys can be found in [the Swagger documentation](https://swagger.io/docs/specification/data-models/oneof-anyof-allof-not/).

        Returns:
            Property names.

        """

        schema = self.resource_cls.schema()
        attributes = schema["properties"]["attributes"]
        if "allOf" in attributes:
            allOf = attributes.pop("allOf")
            for dict_ in allOf:
                attributes.update(dict_)
        if "$ref" in attributes:
            path = attributes["$ref"].split("/")[1:]
            attributes = schema.copy()
            while path:
                next_key = path.pop(0)
                attributes = attributes[next_key]
        return set(attributes["properties"].keys())

    def handle_query_params(
        self, params: Union[EntryListingQueryParams, SingleEntryQueryParams]
    ) -> Tuple[Dict[str, Any]]:
        """Parse and interpret the backend-agnostic query parameter models into a dictionary
        that can be used by the specific backend.

        Note:
            Currently this method returns the pymongo interpretation of the parameters,
            which will need modification for modified for other backends.

        Parameters:
            params (Union[EntryListingQueryParams, SingleEntryQueryParams]): The initialized query parameter model from the server.

        Raises:
            Forbidden: If too large of a page limit is provided.
            BadRequest: If an invalid request is made, e.g., with incorrect fields
                or response format.

        Returns:
            A dictionary representation of the query parameters.

        """
        cursor_kwargs = {}

        if getattr(params, "filter", False):
            tree = self.parser.parse(params.filter)
            cursor_kwargs["filter"] = self.transformer.transform(tree)
        else:
            cursor_kwargs["filter"] = {}

        if (
            getattr(params, "response_format", False)
            and params.response_format != "json"
        ):
            raise BadRequest(
                detail=f"Response format {params.response_format} is not supported, please use response_format='json'"
            )

        if getattr(params, "page_limit", False):
            limit = params.page_limit
            if limit > CONFIG.page_limit_max:
                raise Forbidden(
                    detail=f"Max allowed page_limit is {CONFIG.page_limit_max}, you requested {limit}",
                )
            cursor_kwargs["limit"] = limit
        else:
            cursor_kwargs["limit"] = CONFIG.page_limit

        cursor_kwargs["projection"] = {
            f"{self.resource_mapper.get_backend_field(f)}": True
            for f in self.all_fields
        }

        if "_id" not in cursor_kwargs["projection"]:
            cursor_kwargs["projection"]["_id"] = False

        if getattr(params, "sort", False):
            cursor_kwargs["sort"] = self.parse_sort_params(params.sort)

        if getattr(params, "page_offset", False):
            cursor_kwargs["skip"] = params.page_offset

        if getattr(params, "response_fields", False):
            response_fields = set(params.response_fields.split(","))
            response_fields |= self.resource_mapper.get_required_fields()
        else:
            response_fields = self.all_fields.copy()

        cursor_kwargs["fields"] = response_fields

        return cursor_kwargs

    def parse_sort_params(self, sort_params) -> List[Tuple[str, int]]:
        """Handles any sort parameters passed to the collection,
        resolving aliases and dealing with any invalid fields.

        Raises:
            BadRequest: if an invalid sort is requested.

        Returns:
            A list of tuples containing the aliased field name and
            sort direction encoded as 1 (ascending) or -1 (descending).

        """
        sort_spec = []
        for field in sort_params.split(","):
            sort_dir = 1
            if field.startswith("-"):
                field = field[1:]
                sort_dir = -1
            aliased_field = self.resource_mapper.get_backend_field(field)
            sort_spec.append((aliased_field, sort_dir))

        unknown_fields = [
            field
            for field, _ in sort_spec
            if self.resource_mapper.get_optimade_field(field) not in self.all_fields
        ]

        if unknown_fields:
            error_detail = "Unable to sort on unknown field{} '{}'".format(
                "s" if len(unknown_fields) > 1 else "",
                "', '".join(unknown_fields),
            )

            # If all unknown fields are "other" provider-specific, then only provide a warning
            if all(
                (
                    re.match(r"_[a-z_0-9]+_[a-z_0-9]*", field)
                    and not field.startswith(f"_{self.provider_prefix}_")
                )
                for field in unknown_fields
            ):
                warnings.warn(error_detail, FieldValueNotRecognized)

            # Otherwise, if all fields are unknown, or some fields are unknown and do not
            # have other provider prefixes, then return 400: Bad Request
            else:
                raise BadRequest(detail=error_detail)

        # If at least one valid field has been provided for sorting, then use that
        sort_spec = tuple(
            (field, sort_dir)
            for field, sort_dir in sort_spec
            if field not in unknown_fields
        )

        return sort_spec
