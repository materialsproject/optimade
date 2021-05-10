import json
from pathlib import Path
from typing import Tuple, List, Optional, Dict, Any, Iterable, Union

from optimade.filterparser import LarkParser
from optimade.filtertransformers.elasticsearch import ElasticTransformer
from optimade.server.config import CONFIG
from optimade.server.logger import LOGGER
from optimade.models import EntryResource
from optimade.server.mappers import BaseResourceMapper
from optimade.server.entry_collections import EntryCollection


if CONFIG.database_backend.value == "elastic":
    from elasticsearch import Elasticsearch
    from elasticsearch.helpers import bulk
    from elasticsearch_dsl import Search

    CLIENT = Elasticsearch(hosts=CONFIG.elastic_hosts)
    LOGGER.info("Using: Elasticsearch backend at %s", CONFIG.elastic_hosts)


class ElasticCollection(EntryCollection):
    def __init__(
        self,
        name: str,
        resource_cls: EntryResource,
        resource_mapper: BaseResourceMapper,
        client: Optional["Elasticsearch"] = None,
    ):
        """Initialize the ElasticCollection for the given parameters.

        Parameters:
            name: The name of the collection.
            resource_cls: The type of entry resource that is stored by the collection.
            resource_mapper: A resource mapper object that handles aliases and
                format changes between deserialization and response.
            client: A preconfigured Elasticsearch client.

        """
        self.client = client if client else CLIENT

        self.resource_cls = resource_cls
        self.resource_mapper = resource_mapper
        self.provider_prefix = CONFIG.provider.prefix
        self.provider_fields = CONFIG.provider_fields.get(resource_mapper.ENDPOINT, [])
        self.parser = LarkParser()

        self.transformer = ElasticTransformer(mapper=self.resource_mapper)

        self.name = name

        # If we are creating a new collection from scratch, also create the index,
        # otherwise assume it has already been created externally
        if CONFIG.insert_test_data:
            self.create_optimade_index()

    def count(self, *args, **kwargs) -> int:
        raise NotImplementedError

    def create_optimade_index(self) -> None:
        """Load or create an index that can handle aliased OPTIMADE fields and attach it
        to the current client.

        """
        body = self.predefined_index.get(self.name)
        if body is None:
            body = self.create_elastic_index_from_mapper(
                self.resource_mapper, self.all_fields
            )

        properties = {}
        for field in list(body["mappings"]["doc"]["properties"].keys()):
            properties[self.resource_mapper.get_backend_field(field)] = body[
                "mappings"
            ]["doc"]["properties"].pop(field)
        body["mappings"]["doc"]["properties"] = properties
        self.client.indices.create(index=self.name, body=body, ignore=400)

        LOGGER.debug(f"Created Elastic index for {self.name!r} with body {body}")

    @property
    def predefined_index(self) -> Dict[str, Any]:
        """Loads and returns the default pre-defined index."""
        with open(Path(__file__).parent.joinpath("elastic_indexes.json")) as f:
            index = json.load(f)
        return index

    @staticmethod
    def create_elastic_index_from_mapper(
        resource_mapper: BaseResourceMapper, fields: Iterable[str]
    ) -> Dict[str, Any]:
        """Create a fallback elastic index based on a resource mapper.

        Arguments:
            resource_mapper: The resource mapper to create the index for.
            fields: The list of fields to use in the index.

        Returns:
            The `body` parameter to pass to `client.indices.create(..., body=...)`.

        """
        return {
            "mappings": {
                "doc": {
                    "properties": {
                        resource_mapper.get_optimade_field(field): {"type": "keyword"}
                        for field in fields
                    }
                }
            }
        }

    def __len__(self):
        """Returns the total number of entries in the collection."""
        return Search(using=self.client, index=self.name).execute().hits.total

    def insert(self, data: List[EntryResource]) -> None:
        """Add the given entries to the underlying database.

        Warning:
            No validation is performed on the incoming data.

        Arguments:
            data: The entry resource objects to add to the database.

        """

        def get_id(item):
            if self.name == "links":
                id_ = "%s-%s" % (item["id"], item["type"])
            elif "id" in item:
                id_ = item["id"]
            elif "_id" in item:
                # use the existing MongoDB ids in the test data
                id_ = str(item["_id"])
            else:
                # ES will generate ids
                id_ = None
            item.pop("_id", None)
            return id_

        bulk(
            self.client,
            [
                {
                    "_index": self.name,
                    "_id": get_id(item),
                    "_type": "doc",
                    "_source": item,
                }
                for item in data
            ],
        )

    def _run_db_query(
        self, criteria: Dict[str, Any], single_entry=False
    ) -> Tuple[Union[List[Dict[str, Any]], Dict[str, Any]], int, bool]:
        """Run the query on the backend and collect the results.

        Arguments:
            criteria: A dictionary representation of the query parameters.
            single_entry: Whether or not the caller is expecting a single entry response.

        Returns:
            The list of entries from the database (without any re-mapping), the total number of
            entries matching the query and a boolean for whether or not there is more data available.

        """

        search = Search(using=self.client, index=self.name)

        if criteria.get("filter", False):
            search = search.query(criteria["filter"])

        page_offset = criteria.get("skip", 0)
        limit = criteria.get("limit", CONFIG.page_limit)

        all_aliased_fields = [
            self.resource_mapper.get_backend_field(field) for field in self.all_fields
        ]
        search = search.source(includes=all_aliased_fields)

        elastic_sort = [
            {field: {"order": "desc" if sort_dir == -1 else "asc"}}
            for field, sort_dir in criteria.get("sort", {})
        ]
        if not elastic_sort:
            elastic_sort = {
                self.resource_mapper.get_backend_field("id"): {"order": "asc"}
            }

        search = search.sort(*elastic_sort)

        search = search[page_offset : page_offset + limit]
        response = search.execute()

        results = [hit.to_dict() for hit in response.hits]

        if not single_entry:
            data_returned = response.hits.total
            more_data_available = page_offset + limit < data_returned
        else:
            # SingleEntryQueryParams, e.g., /structures/{entry_id}
            data_returned = len(results)
            more_data_available = False

        return results, data_returned, more_data_available
