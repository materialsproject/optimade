# pylint: disable=no-self-argument
from enum import Enum
from pathlib import Path
import warnings
from typing import Any, Dict, List, Optional, Tuple

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

from pydantic import (  # pylint: disable=no-name-in-module
    AnyHttpUrl,
    BaseSettings,
    Field,
    root_validator,
    validator,
)
from pydantic.env_settings import SettingsSourceCallable

from optimade import __version__
from optimade.models import Implementation, Provider


DEFAULT_CONFIG_FILE_PATH: str = str(Path.home().joinpath(".optimade.json"))
"""Default configuration file path.

This variable is used as the fallback value if the environment variable `OPTIMADE_CONFIG_FILE` is
not set.

!!! note
    It is set to: `pathlib.Path.home()/.optimade.json`

    For Unix-based systems (Linux) this will be equivalent to `~/.optimade.json`.

"""


class LogLevel(Enum):
    """Replication of logging LogLevels

    - `notset`
    - `debug`
    - `info`
    - `warning`
    - `error`
    - `critical`

    """

    NOTSET = "notset"
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class SupportedBackend(Enum):
    """Enumeration of supported database backends

    - `elastic`: [Elasticsearch](https://www.elastic.co/).
    - `mongodb`: [MongoDB](https://www.mongodb.com/).
    - `mongomock`: Also MongoDB, but instead of using the
        [`pymongo`](https://pymongo.readthedocs.io/) driver to connect to a live Mongo database
        instance, this will use the [`mongomock`](https://github.com/mongomock/mongomock) driver,
        creating an in-memory database, which is mainly used for testing.

    """

    ELASTIC = "elastic"
    MONGODB = "mongodb"
    MONGOMOCK = "mongomock"


def config_file_settings(settings: BaseSettings) -> Dict[str, Any]:
    """Configuration file settings source.

    Based on the example in the
    [pydantic documentation](https://pydantic-docs.helpmanual.io/usage/settings/#adding-sources),
    this function loads ServerConfig settings from a configuration file.

    The file must be of either type JSON or YML/YAML.

    Parameters:
        settings: The `pydantic.BaseSettings` class using this function as a
            `pydantic.SettingsSourceCallable`.

    Returns:
        Dictionary of settings as read from a file.

    """
    import json
    import os
    import yaml

    encoding = settings.__config__.env_file_encoding
    config_file = Path(os.getenv("OPTIMADE_CONFIG_FILE", DEFAULT_CONFIG_FILE_PATH))

    res = {}
    if config_file.is_file():
        config_file_content = config_file.read_text(encoding=encoding)

        try:
            res = json.loads(config_file_content)
        except json.JSONDecodeError as json_exc:
            try:
                # This can essentially also load JSON files, as JSON is a subset of YAML v1,
                # but I suspect it is not as rigorous
                res = yaml.safe_load(config_file_content)
            except yaml.YAMLError as yaml_exc:
                warnings.warn(
                    f"Unable to parse config file {config_file} as JSON or YAML, using the "
                    "default settings instead..\n"
                    f"Errors:\n  JSON:\n{json_exc}.\n\n  YAML:\n{yaml_exc}"
                )
    else:
        warnings.warn(
            f"Unable to find config file at {config_file}, using the default settings instead."
        )

    if res is None:
        # This can happen if the yaml loading doesn't succeed properly, e.g., if the file is empty.
        warnings.warn(
            "Unable to load any settings from {config_file}, using the default settings instead."
        )
        res = {}

    return res


class ServerConfig(BaseSettings):
    """This class stores server config parameters in a way that
    can be easily extended for new config file types.

    """

    debug: bool = Field(
        False,
        description="Turns on Debug Mode for the OPTIMADE Server implementation",
    )

    insert_test_data: bool = Field(
        True,
        description=(
            "Insert test data into each collection on server initialisation. If true, the "
            "configured backend will be populated with test data on server start. Should be "
            "disabled for production usage."
        ),
    )

    use_real_mongo: Optional[bool] = Field(
        None, description="DEPRECATED: force usage of MongoDB over any other backend."
    )

    database_backend: SupportedBackend = Field(
        SupportedBackend.MONGOMOCK,
        description="Which database backend to use out of the supported backends.",
    )

    elastic_hosts: Optional[List[Dict]] = Field(
        None, description="Host settings to pass through to the `Elasticsearch` class."
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
        description=(
            "ID of /links endpoint resource for the chosen default OPTIMADE implementation (only "
            "relevant for the index meta-database)"
        ),
    )
    root_path: Optional[str] = Field(
        None,
        description=(
            "Sets the FastAPI app `root_path` parameter. This can be used to serve the API under a"
            " path prefix behind a proxy or as a sub-application of another FastAPI app. See "
            "https://fastapi.tiangolo.com/advanced/sub-applications/#technical-details-root_path "
            "for details."
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
        description=(
            "A list of additional fields to be served with the provider's prefix attached, "
            "broken down by endpoint."
        ),
    )
    aliases: Dict[Literal["links", "references", "structures"], Dict[str, str]] = Field(
        {},
        description=(
            "A mapping between field names in the database with their corresponding OPTIMADE field"
            " names, broken down by endpoint."
        ),
    )
    length_aliases: Dict[
        Literal["links", "references", "structures"], Dict[str, str]
    ] = Field(
        {},
        description=(
            "A mapping between a list property (or otherwise) and an integer property that defines"
            " the length of that list, for example elements -> nelements. The standard aliases are"
            " applied first, so this dictionary must refer to the API fields, not the database "
            "fields."
        ),
    )
    index_links_path: Path = Field(
        Path(__file__).parent.joinpath("index_links.json"),
        description=(
            "Absolute path to a JSON file containing the MongoDB collecton of links entries "
            "(documents) to serve under the /links endpoint of the index meta-database. "
            "NB! As suggested in the previous sentence, these will only be served when using a "
            "MongoDB-based backend."
        ),
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
    def use_real_mongo_override(cls, values):
        """Overrides the `database_backend` setting with MongoDB and
        raises a deprecation warning.

        """
        use_real_mongo = values.pop("use_real_mongo", None)
        if use_real_mongo is not None:
            warnings.warn(
                "'use_real_mongo' is deprecated, please set the appropriate 'database_backend' "
                "instead.",
                DeprecationWarning,
            )

            if use_real_mongo:
                values["database_backend"] = SupportedBackend.MONGODB

        return values

    class Config:
        """
        This is a pydantic model Config object that modifies the behaviour of
        ServerConfig by adding a prefix to the environment variables that
        override config file values. It has nothing to do with the OPTIMADE
        config.

        """

        env_prefix = "optimade_"
        extra = "allow"
        env_file_encoding = "utf-8"

        @classmethod
        def customise_sources(
            cls,
            init_settings: SettingsSourceCallable,
            env_settings: SettingsSourceCallable,
            file_secret_settings: SettingsSourceCallable,
        ) -> Tuple[SettingsSourceCallable, ...]:
            """
            **Priority of config settings sources**:

            1. Passed arguments upon initialization of
               [`ServerConfig`][optimade.server.config.ServerConfig].
            2. Environment variables, matching the syntax: `"OPTIMADE_"` or `"optimade_"` +
               `<config_name>`, e.g., `OPTIMADE_LOG_LEVEL=debug` or
               `optimade_log_dir=~/logs_dir/optimade/`.
            3. Configuration file (JSON/YAML) taken from:
               1. Environment variable `OPTIMADE_CONFIG_FILE`.
               2. Default location (see
                  [DEFAULT_CONFIG_FILE_PATH][optimade.server.config.DEFAULT_CONFIG_FILE_PATH]).
            4. Settings from secret file (see
               [pydantic documentation](https://pydantic-docs.helpmanual.io/usage/settings/#secret-support)
               for more information).

            """
            return (
                init_settings,
                env_settings,
                config_file_settings,
                file_secret_settings,
            )


CONFIG = ServerConfig()
