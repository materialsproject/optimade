<img width="10%" align="left" src="images/optimade_logo_180x180.svg">

# OPTIMADE Python tools

| Latest release | Build status | Activity |
|:--------------:|:------------:|:--------:|
| [![PyPI Version](https://img.shields.io/pypi/v/optimade?logo=pypi)](https://pypi.org/project/optimade/)<br>[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/optimade?logo=python)](https://pypi.org/project/optimade/)<br>[![OPTIMADE](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/Materials-Consortia/optimade-python-tools/master/optimade-version.json)](https://github.com/Materials-Consortia/OPTIMADE/) | [![Build Status](https://img.shields.io/github/workflow/status/Materials-Consortia/optimade-python-tools/CI%20tests?logo=github)](https://github.com/Materials-Consortia/optimade-python-tools/actions?query=branch%3Amaster+)<br>[![codecov](https://codecov.io/gh/Materials-Consortia/optimade-python-tools/branch/master/graph/badge.svg)](https://codecov.io/gh/Materials-Consortia/optimade-python-tools)<br>[![Heroku App Status](https://heroku-shields.herokuapp.com/optimade??logo=heroku)](https://optimade.herokuapp.com) | [![Commit Activity](https://img.shields.io/github/commit-activity/m/Materials-Consortia/optimade-python-tools?logo=github)](https://github.com/Materials-Consortia/optimade-python-tools/pulse)<br>[![Last Commit](https://img.shields.io/github/last-commit/Materials-Consortia/optimade-python-tools/master?logo=github)](https://github.com/Materials-Consortia/optimade-python-tools/commits/master)<br>[![Contributors](https://badgen.net/github/contributors/Materials-Consortia/optimade-python-tools?icon=github)](https://github.com/Materials-Consortia/optimade-python-tools/graphs/contributors) |


The aim of OPTIMADE is to develop a common API, compliant with the [JSON API 1.0](http://jsonapi.org/format/1.0/) specification.
This is to enable interoperability among databases that contain calculated properties of existing and hypothetical materials.

This repository contains a library of tools for implementing and consuming [OPTIMADE](https://www.optimade.org) APIs using Python.
It also contains a server validator tool, which may be called from the shell or used as a GitHub Action from [optimade-validator-action](https://github.com/Materials-Consortia/optimade-validator-action).

_Disclaimer_: While the package supports `elasticsearch-dsl` v6 & v7 and `django` v2 & v3, all tests are performed with the latest supported version.
If you experience any issues with the older versions, you are most welcome to contribute to the repository (see below under [Contributing](#contributing)).

## Status

Whilst v1.0 of the OPTIMADE specification has been released, this repository is **under development**.
Outstanding features required for compliance with OPTIMADE v1.0 can be tracked with the OPTIMADE v1.0 label on [GitHub](https://github.com/Materials-Consortia/optimade-python-tools/issues?q=is%3Aopen+is%3Aissue+label%3A%22OPTIMADE+v1.0%22), which can be further filtered by backend.
The release history and changelog can be found in [the changelog](CHANGELOG.md).

## Documentation

This document, guides, and the full module API documentation can be found online at [https://optimade.org/optimade-python-tools](https://optimade.org/optimade-python-tools).

## Installation

Detailed instructions for installing and running the index meta-database and the main API can be found in [the installation documentation](INSTALL.md).

The latest stable version of this package can be obtained from [PyPI](https://pypi.org/project/optimade) `pip install optimade`.
The latest development version of this package can be installed from the master branch of this repository `git clone https://github.com/Materials-Consortia/optimade-python-tools`.

## Contributing

Contribution tips and guidelines can be found in [the contributing guidelines](CONTRIBUTING.md).

## Links

- [OPTIMADE Specification](https://github.com/Materials-Consortia/OPTIMADE/blob/develop/optimade.rst), the human-readable specification that this library is based on.
- [optimade-validator-action](https://github.com/Materials-Consortia/optimade-validator-action), a GitHub action that can be used to validate implementations from a URL (using the validator from this repo).
- [OpenAPI](https://github.com/OAI/OpenAPI-Specification), the machine-readable format used to specify the OPTIMADE API in [`openapi.json`](openapi/openapi.json) and [`index_openapi.json`](openapi/index_openapi.json).
- [Interactive documentation](https://petstore.swagger.io/?url=https://raw.githubusercontent.com/Materials-Consortia/optimade-python-tools/master/openapi/openapi.json) generated from [`openapi.json`](openapi/openapi.json) (see also [interactive JSON editor](https://editor.swagger.io/?url=https://raw.githubusercontent.com/Materials-Consortia/optimade-python-tools/master/openapi/openapi.json)).
- [pydantic](https://pydantic-docs.helpmanual.io/), the library used for generating the OpenAPI schema from [Python models](https://www.optimade.org/optimade-python-tools/all_models/).
- [FastAPI](https://fastapi.tiangolo.com/), the framework used for generating the reference implementation expressed by the [`openapi.json`](openapi/openapi.json) specification.
- [lark](https://github.com/lark-parser/lark), the library used to parse the filter language in OPTIMADE queries.
