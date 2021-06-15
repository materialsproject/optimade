# Integrate with an existing web application

`optimade-python-tools` (OPT) can be run as a standalone web application that serves the OPTIMADE API based on a pre-configured MongoDB backend.
In this document, we are going to use OPT differently and use it to add an OPTIMADE API implementation alongside an existing API employing an Elasticsearch storage layer.

Let's assume we already have a *FastAPI* application that runs an unrelated web service, and that we use an Elasticsearch backend that contains all structure data, but not necessarily in a form that OPTIMADE expects.

## Providing an `optimade-python-tools` configuration

OPT can read its configuration from a JSON file.
It uses the `OPTIMADE_CONFIG_FILE` environment variable (or a default path) to find the config file.
If you run OPT from another application, you might want to provide this config file as part of the source code and not via environment variables.
Let's say you have a file `optimade_config.json` as part of the Python module that you use to create your OPT.

!!! tip
    You can find more detailed information about configuring OPT in the [Configuration](../configuration.md) section.

Before importing any OPT packages, you can set the `OPTIMADE_CONFIG_FILE` environment variable to link OPT to your config file:

```python
import os
import sys

os.environ['OPTIMADE_CONFIG_FILE'] = os.path.join(
    os.path.dirname(__file__), 'optimade_config.json'
)
```

## Customize the [`EntryCollection`][optimade.server.entry_collections.entry_collections.EntryCollection] implementation

Let's assume that your Elasticsearch backend stores structure data different enough that you need to provide your own custom implementation.
The following code customizes the used [`EntryCollection`][optimade.server.entry_collections.entry_collections.EntryCollection] class for structures, while keeping the default *mongomock* implementation (using [`MongoCollection`][optimade.server.entry_collections.mongo.MongoCollection]) for all other entry types.

```python
from optimade.server.routers import structures

structures.structures_coll = MyElasticsearchStructureCollection()
```

You can imagine that `MyElasticsearchStructureCollection` either sub-classes the default OPT Elasticsearch implementation or sub-classes `EntryCollection`, depending on how deeply you need to customize the default OPT behavior.

## Mounting the OPTIMADE Python tools *FastAPI* app into an existing *FastAPI* app

Let's assume you have an existing *FastAPI* app `my_app`.
It already adds a few routers under certain path prefixes and now you want to add an OPTIMADE implementation under the path prefix `/optimade`.
First, you have to set the `root_path` in the OPT configuration.
Now, the OPT app expects all requests being prefixed with `/optimade`.
Of course, you can also set the value in your OPT config file.
Second, you simply mount the OPT app into `my_app`:

```python
from optimade.server.config import CONFIG
CONFIG.root_path = "/optimade"

from optimade.server import main as optimade

optimade.add_major_version_base_url(optimade.app)
my_app.mount("/optimade", optimade.app)
```

See also the *FastAPI* documentation on [sub-applications](https://fastapi.tiangolo.com/advanced/sub-applications/).

If you run `my_app`, it will still serve all its routers as before and in addition it will also serve all OPT provided routes under `/optimade/*` and `/optimade/v1/*`.
