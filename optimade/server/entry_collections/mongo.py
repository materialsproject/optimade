import os

from typing import Tuple, List, Union
import mongomock
import pymongo.collection
from fastapi import HTTPException

from optimade.filterparser import LarkParser
from optimade.filtertransformers.mongo import MongoTransformer
from optimade.models import EntryResource
from optimade.server.config import CONFIG
from optimade.server.entry_collections import EntryCollection
from optimade.server.logger import LOGGER
from optimade.server.mappers import BaseResourceMapper
from optimade.server.query_params import EntryListingQueryParams, SingleEntryQueryParams

try:
    CI_FORCE_MONGO = bool(int(os.environ.get("OPTIMADE_CI_FORCE_MONGO", 0)))
except (TypeError, ValueError):  # pragma: no cover
    CI_FORCE_MONGO = False


if CONFIG.use_real_mongo or CI_FORCE_MONGO:
    from pymongo import MongoClient

    client = MongoClient(CONFIG.mongo_uri)
    LOGGER.info("Using: Real MongoDB (pymongo)")
else:
    from mongomock import MongoClient

    client = MongoClient()
    LOGGER.info("Using: Mock MongoDB (mongomock)")


class MongoCollection(EntryCollection):
    """Class for querying MongoDB collections (implemented by either pymongo or mongomock)
    containing serialized [`EntryResource`][optimade.models.entries.EntryResource]s objects.

    """

    def __init__(
        self,
        collection: Union[
            pymongo.collection.Collection, mongomock.collection.Collection
        ],
        resource_cls: EntryResource,
        resource_mapper: BaseResourceMapper,
    ):
        """Initialize the MongoCollection for the given parameters.

        Parameters:
            collection (Union[pymongo.collection.Collection, mongomock.collection.Collection]):
                The backend-specific collection.
            resource_cls (EntryResource): The `EntryResource` model
                that is stored by the collection.
            resource_mapper (BaseResourceMapper): A resource mapper
                object that handles aliases and format changes between
                deserialization and response.

        """
        super().__init__(
            collection,
            resource_cls,
            resource_mapper,
            MongoTransformer(mapper=resource_mapper),
        )

        self.parser = LarkParser(version=(1, 0, 0), variant="default")

        # check aliases do not clash with mongo operators
        self._check_aliases(self.resource_mapper.all_aliases())
        self._check_aliases(self.resource_mapper.all_length_aliases())

    def __len__(self) -> int:
        return self.collection.estimated_document_count()

    def count(self, **kwargs) -> int:
        """Returns the number of entries matching the query specified
        by the keyword arguments.

        Parameters:
            kwargs (dict): Query parameters as keyword arguments. The keys
                'filter', 'skip', 'limit', 'hint' and 'maxTimeMS' will be passed
                to the `pymongo.collection.Collection.count_documents` method.

        """
        for k in list(kwargs.keys()):
            if k not in ("filter", "skip", "limit", "hint", "maxTimeMS"):
                del kwargs[k]
        if "filter" not in kwargs:  # "filter" is needed for count_documents()
            kwargs["filter"] = {}
        return self.collection.count_documents(**kwargs)

    def find(
        self, params: Union[EntryListingQueryParams, SingleEntryQueryParams]
    ) -> Tuple[List[EntryResource], int, bool, set]:
        """Perform the query on the underlying MongoCollection, handling projection
        and pagination of the output.

        Returns:
            Tuple[List[EntryResource], int, bool, set]: A list of entry resource objects, the number of returned entries,
            whether more are available with pagination, fields.

        """

        criteria = self.handle_query_params(params)

        all_fields = criteria.pop("fields")
        if getattr(params, "response_fields", False):
            fields = set(params.response_fields.split(","))
            fields |= self.resource_mapper.get_required_fields()
        else:
            fields = all_fields.copy()

        results = []
        for doc in self.collection.find(**criteria):
            if criteria.get("projection", {}).get("_id"):
                doc["_id"] = str(doc["_id"])
            results.append(self.resource_cls(**self.resource_mapper.map_back(doc)))

        nresults_now = len(results)
        if isinstance(params, EntryListingQueryParams):
            criteria_nolimit = criteria.copy()
            criteria_nolimit.pop("limit", None)
            data_returned = self.count(**criteria_nolimit)
            more_data_available = nresults_now < data_returned
        else:
            # SingleEntryQueryParams, e.g., /structures/{entry_id}
            data_returned = nresults_now
            more_data_available = False
            if nresults_now > 1:
                raise HTTPException(
                    status_code=404,
                    detail=f"Instead of a single entry, {nresults_now} entries were found",
                )
            results = results[0] if results else None

        return results, data_returned, more_data_available, all_fields - fields

    def _check_aliases(self, aliases):
        """ Check that aliases do not clash with mongo keywords. """
        if any(
            alias[0].startswith("$") or alias[1].startswith("$") for alias in aliases
        ):
            raise RuntimeError(f"Cannot define an alias starting with a '$': {aliases}")
