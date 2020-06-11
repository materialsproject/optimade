# pylint: disable=line-too-long
import json
import os
from pathlib import Path

from lark.exceptions import VisitError

from pydantic import ValidationError
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError, StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware

from optimade import __api_version__, __version__
import optimade.server.exception_handlers as exc_handlers

from .entry_collections import MongoCollection
from .config import CONFIG
from .middleware import EnsureQueryParamIntegrity
from .routers import info, links, references, structures, landing
from .routers.utils import get_providers, BASE_URL_PREFIXES


if CONFIG.debug:  # pragma: no cover
    print("DEBUG MODE")


app = FastAPI(
    title="OPTIMADE API",
    description=(
        f"""The [Open Databases Integration for Materials Design (OPTIMADE) consortium](https://www.optimade.org/) aims to make materials databases interoperational by developing a common REST API.

This specification is generated using [`optimade-python-tools`](https://github.com/Materials-Consortia/optimade-python-tools/tree/v{__version__}) v{__version__}."""
    ),
    version=__api_version__,
    docs_url=f"{BASE_URL_PREFIXES['major']}/extensions/docs",
    redoc_url=f"{BASE_URL_PREFIXES['major']}/extensions/redoc",
    openapi_url=f"{BASE_URL_PREFIXES['major']}/extensions/openapi.json",
)


if not CONFIG.use_real_mongo:
    import bson.json_util
    import optimade.server.data as data
    from .routers import ENTRY_COLLECTIONS

    def load_entries(endpoint_name: str, endpoint_collection: MongoCollection):
        print(f"loading test {endpoint_name}...")

        endpoint_collection.collection.insert_many(getattr(data, endpoint_name, []))
        if endpoint_name == "links":
            print("adding Materials-Consortia providers to links from optimade.org")
            endpoint_collection.collection.insert_many(
                bson.json_util.loads(bson.json_util.dumps(get_providers()))
            )
        print(f"done inserting test {endpoint_name}...")

    for name, collection in ENTRY_COLLECTIONS.items():
        load_entries(name, collection)


# Add various middleware
app.add_middleware(CORSMiddleware, allow_origins=["*"])
app.add_middleware(EnsureQueryParamIntegrity)


# Add various exception handlers
app.add_exception_handler(StarletteHTTPException, exc_handlers.http_exception_handler)
app.add_exception_handler(
    RequestValidationError, exc_handlers.request_validation_exception_handler
)
app.add_exception_handler(ValidationError, exc_handlers.validation_exception_handler)
app.add_exception_handler(VisitError, exc_handlers.grammar_not_implemented_handler)
app.add_exception_handler(NotImplementedError, exc_handlers.not_implemented_handler)
app.add_exception_handler(Exception, exc_handlers.general_exception_handler)


# Add various endpoints to `/vMAJOR`
app.include_router(info.router, prefix=BASE_URL_PREFIXES["major"])
app.include_router(links.router, prefix=BASE_URL_PREFIXES["major"])
app.include_router(references.router, prefix=BASE_URL_PREFIXES["major"])
app.include_router(structures.router, prefix=BASE_URL_PREFIXES["major"])


# Add the router for the landing page for all prefixes
app.include_router(landing.router)
app.include_router(landing.router, prefix=BASE_URL_PREFIXES["major"])


def add_optional_versioned_base_urls(app: FastAPI):
    """Add the following OPTIONAL prefixes/base URLs to server:
    ```
        /vMajor.Minor
        /vMajor.Minor.Patch
    ```
    """
    for version in ("minor", "patch"):
        app.include_router(info.router, prefix=BASE_URL_PREFIXES[version])
        app.include_router(links.router, prefix=BASE_URL_PREFIXES[version])
        app.include_router(references.router, prefix=BASE_URL_PREFIXES[version])
        app.include_router(structures.router, prefix=BASE_URL_PREFIXES[version])
        app.include_router(landing.router, prefix=BASE_URL_PREFIXES[version])


def update_schema(app: FastAPI):
    """Update OpenAPI schema in file 'local_openapi.json'"""
    package_root = Path(__file__).parent.parent.parent.resolve()
    if not package_root.joinpath("openapi").exists():
        os.mkdir(package_root.joinpath("openapi"))

    # add list of servers to openapi spec
    openapi = app.openapi()
    with open(CONFIG.cors_providers_path) as f:
        config_providers = json.load(f)

    openapi.update(config_providers)
    with open(package_root.joinpath("openapi/local_openapi.json"), "w") as f:
        json.dump(openapi, f, indent=2)


@app.on_event("startup")
async def startup_event():
    # Update OpenAPI schema on versioned base URL `/vMAJOR`
    update_schema(app)
    # Add API endpoints for OPTIONAL base URLs `/vMAJOR.MINOR` and `/vMAJOR.MINOR.PATCH`
    add_optional_versioned_base_urls(app)
