# pylint: disable=no-self-argument
import json
import logging
from typing import Optional, Dict, List


try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal
from pathlib import Path

from pydantic import BaseSettings, Field, root_validator

from optimade import __version__
from optimade.models import Implementation, Provider


DEFAULT_CONFIG_FILE_PATH = str(Path.home().joinpath(".optimade.json"))
logger = logging.getLogger("optimade")


class NoFallback(Exception):
    """No fallback value can be found."""


class ServerConfig(BaseSettings):
    """ This class stores server config parameters in a way that
    can be easily extended for new config file types.

    """

    config_file: str = Field(
        DEFAULT_CONFIG_FILE_PATH, description="File to load alternative defaults from",
    )
    debug: bool = Field(
        False, description="Turns on Debug Mode for the OPTIMADE Server implementation"
    )
    use_real_mongo: bool = Field(
        False, description="Use a real Mongo server rather than MongoMock"
    )
    mongo_database: str = Field(
        "optimade", description="Mongo database for collection data"
    )
    mongo_uri: str = Field("localhost:27017", description="URI for the Mongo server")
    links_collection: str = Field(
        "links", description="Mongo collection name for /links endpoint resources"
    )
    references_collection: str = Field(
        "references",
        description="Mongo collection name for /references endpoint resources",
    )
    structures_collection: str = Field(
        "structures",
        description="Mongo collection name for /structures endpoint resources",
    )
    page_limit: int = Field(20, description="Default number of resources per page")
    page_limit_max: int = Field(
        500, description="Max allowed number of resources per page"
    )
    default_db: str = Field(
        "test_server",
        description="ID of /links endpoint resource for the chosen default OPTIMADE implementation (only relevant for the index meta-database)",
    )
    base_url: Optional[str] = Field(
        None, description="Base URL for this implementation"
    )
    implementation: Implementation = Field(
        Implementation(
            name="Example implementation",
            version=__version__,
            source_url="https://github.com/Materials-Consortia/optimade-python-tools",
            maintainer=None,
        ),
        description="Introspective information about this OPTIMADE implementation",
    )
    provider: Provider = Field(
        Provider(
            prefix="exmpl",
            name="Example provider",
            description="Provider used for examples, not to be assigned to a real database",
            homepage="https://example.com",
            index_base_url="http://localhost:5001",
        ),
        description="General information about the provider of this OPTIMADE implementation",
    )
    provider_fields: Dict[
        Literal["links", "references", "structures"], List[str]
    ] = Field(
        {},
        description="A list of additional fields to be served with the provider's prefix attached, broken down by endpoint.",
    )
    aliases: Dict[Literal["links", "references", "structures"], Dict[str, str]] = Field(
        {},
        description="A mapping between field names in the database with their corresponding OPTIMADE field names, broken down by endpoint.",
    )

    length_aliases: Dict[
        Literal["links", "references", "structures"], Dict[str, str]
    ] = Field(
        {},
        description=(
            "A mapping between a list property (or otherwise) and an integer property that defines the length of that list, "
            "for example elements -> nelements. The standard aliases are applied first, so this dictionary must refer to the "
            "API fields, not the database fields."
        ),
    )

    index_links_path: Path = Field(
        Path(__file__).parent.joinpath("index_links.json"),
        description="Absolute path to a JSON file containing the MongoDB collection of /links resources for the index meta-database",
    )

    cors_providers_path: Path = Field(
        Path(__file__).parent.joinpath("cors_providers.json"),
        description="Absolute path to a JSON file containing a list of providers to add to the openapi.json file.",
    )

    @root_validator(pre=True)
    def load_default_settings(cls, values):  # pylint: disable=no-self-argument
        """
        Loads settings from a root file if available and uses that as defaults in
        place of built in defaults
        """
        config_file_path = Path(values.get("config_file", DEFAULT_CONFIG_FILE_PATH))

        new_values = {}

        if config_file_path.exists() and config_file_path.is_file():
            logger.debug("Found config file at: %s", config_file_path)
            with open(config_file_path) as f:
                new_values = json.load(f)
        else:
            logger.debug(  # pragma: no cover
                "Did not find config file at: %s", config_file_path
            )

        new_values.update(values)

        return new_values

    class Config:
        env_prefix = "optimade_"


CONFIG = ServerConfig()
