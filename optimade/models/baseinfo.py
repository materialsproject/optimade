# pylint: disable=no-self-argument,no-name-in-module
import re

from typing import Dict, List, Optional
from pydantic import BaseModel, AnyHttpUrl, Field, validator, root_validator

from .jsonapi import Resource


__all__ = ("AvailableApiVersion", "BaseInfoAttributes", "BaseInfoResource")


class AvailableApiVersion(BaseModel):
    """A JSON object containing information about an available API version"""

    url: AnyHttpUrl = Field(
        ...,
        description="A string specifying a versioned base URL that MUST adhere to the rules in section Base URL",
        pattern=r".+/v[0-1](\.[0-9]+)*/?$",
    )

    version: str = Field(
        ...,
        description="A string containing the full version number of the API served at that versioned base URL. "
        "The version number string MUST NOT be prefixed by, e.g., 'v'.",
        # officially recommended semver regexp from https://semver.org/#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string
        pattern=r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$",
    )

    @validator("url")
    def url_must_be_versioned_base_url(cls, v):
        """The URL must be a valid versioned Base URL"""
        if not re.match(r".+/v[0-1](\.[0-9]+)*/?$", v):
            raise ValueError(f"url MUST be a versioned base URL. It is: {v}")
        return v

    @root_validator(pre=False, skip_on_failure=True)
    def crosscheck_url_and_version(cls, values):
        """ Check that URL version and API version are compatible. """
        url_version = (
            values["url"]
            .split("/")[-2 if values["url"].endswith("/") else -1]
            .replace("v", "")
        )
        url_version = tuple(int(val) for val in url_version.split("."))
        api_version = tuple(int(val) for val in values["version"].split("."))
        if any(a != b for a, b in zip(url_version, api_version)):
            raise ValueError(
                f"API version {api_version} is not compatible with url version {url_version}."
            )
        return values


class BaseInfoAttributes(BaseModel):
    """Attributes for Base URL Info endpoint"""

    api_version: str = Field(
        ..., description="Presently used version of the OPTIMADE API"
    )
    available_api_versions: List[AvailableApiVersion] = Field(
        ...,
        description="A list of dictionaries of available API versions at other base URLs",
    )
    formats: List[str] = Field(
        default=["json"], description="List of available output formats."
    )
    available_endpoints: List[str] = Field(
        ...,
        description="List of available endpoints (i.e., the string to be appended to the versioned base URL).",
    )
    entry_types_by_format: Dict[str, List[str]] = Field(
        ..., description="Available entry endpoints as a function of output formats."
    )
    is_index: Optional[bool] = Field(
        default=False,
        description="If true, this is an index meta-database base URL (see section Index Meta-Database). "
        "If this member is not provided, the client MUST assume this is not an index meta-database base URL "
        "(i.e., the default is for `is_index` to be `false`).",
    )

    @validator("entry_types_by_format", check_fields=False)
    def formats_and_endpoints_must_be_valid(cls, v, values):
        for format_, endpoints in v.items():
            if format_ not in values["formats"]:
                raise ValueError(f"'{format_}' must be listed in formats to be valid")
            for endpoint in endpoints:
                if endpoint not in values["available_endpoints"]:
                    raise ValueError(
                        f"'{endpoint}' must be listed in available_endpoints to be valid"
                    )
        return v


class BaseInfoResource(Resource):
    id: str = Field(default="/", const=True)
    type: str = Field(default="info", const=True)
    attributes: BaseInfoAttributes = Field(...)
