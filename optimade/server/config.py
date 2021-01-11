# pylint: disable=no-self-argument
from enum import Enum
import json
import warnings
from typing import Optional, Dict, List

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal
from pathlib import Path

from pydantic import (  # pylint: disable=no-name-in-module
    BaseSettings,
    Field,
    root_validator,
    AnyHttpUrl,
    validator,
)

from optimade import __version__
from optimade.models import Implementation, Provider


DEFAULT_CONFIG_FILE_PATH = str(Path.home().joinpath(".optimade.json"))


class LogLevel(Enum):
    """Replication of logging LogLevels"""

    NOTSET = "notset"
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ServerConfig(BaseSettings):
    """This class stores server config parameters in a way that
    can be easily extended for new config file types.

    """

    config_file: Optional[str] = Field(
        None, description="File to load alternative defaults from"
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
    root_path: Optional[str] = Field(
        None,
        description=(
            "Sets the FastAPI app `root_path` parameter. This can be used to serve the API under a "
            "path prefix behind a proxy or as a sub-application of another FastAPI app. "
            "See https://fastapi.tiangolo.com/advanced/sub-applications/#technical-details-root_path for details."
        ),
    )
    base_url: Optional[str] = Field(
        None, description="Base URL for this implementation"
    )
    implementation: Implementation = Field(
        Implementation(
            name="OPTIMADE Python Tools",
            version=__version__,
            source_url="https://github.com/Materials-Consortia/optimade-python-tools",
            maintainer={"email": "dev@optimade.org"},
        ),
        description="Introspective information about this OPTIMADE implementation",
    )
    index_base_url: Optional[AnyHttpUrl] = Field(
        None,
        description="An optional link to the base URL for the index meta-database of the provider.",
    )
    provider: Provider = Field(
        Provider(
            prefix="exmpl",
            name="Example provider",
            description="Provider used for examples, not to be assigned to a real database",
            homepage="https://example.com",
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
    log_level: LogLevel = Field(
        LogLevel.INFO, description="Logging level for the OPTIMADE server."
    )
    log_dir: Path = Field(
        Path("/var/log/optimade/"),
        description="Folder in which log files will be saved.",
    )

    @validator("implementation", pre=True)
    def set_implementation_version(cls, v):
        """Set defaults and modify bypassed value(s)"""
        res = {"version": __version__}
        res.update(v)
        return res

    @root_validator(pre=True)
    def load_settings(cls, values):
        """
        Loads settings from a JSON config file, if available, and uses them in place
        of the built-in defaults.
        """
        config_file_path = Path(values.get("config_file", DEFAULT_CONFIG_FILE_PATH))

        new_values = {}

        if config_file_path.is_file():
            try:
                with open(config_file_path) as f:
                    new_values = json.load(f)
            except json.JSONDecodeError as exc:
                warnings.warn(
                    f"Unable to parse config file {config_file_path} as JSON. Error: {exc}."
                )

        else:
            if DEFAULT_CONFIG_FILE_PATH != str(config_file_path):
                warnings.warn(
                    f"Unable to find config file in requested location {config_file_path}, "
                    "using the built-in default settings instead."
                )
            else:
                warnings.warn(
                    f"Unable to find config file in default location {DEFAULT_CONFIG_FILE_PATH}, "
                    "using the built-in default settings instead."
                )

        if not new_values:
            values["config_file"] = None

        new_values.update(values)

        return new_values

    class Config:
        """
        This is a pydantic model Config object that modifies the behaviour of
        ServerConfig by adding a prefix to the environment variables that
        override config file values. It has nothing to do with the OPTIMADE
        config.

        """

        env_prefix = "optimade_"


CONFIG = ServerConfig()
