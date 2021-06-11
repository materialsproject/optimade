"""This module contains the
[`ImplementationValidator`][optimade.validator.validator.ImplementationValidator]
class that can be pointed at an OPTIMADE implementation and validated
against the specification via the pydantic models implemented in this package.

"""
# pylint: disable=import-outside-toplevel

import re
import sys
import logging
import random
import urllib.parse
import dataclasses
from typing import Union, Tuple, Any, List, Dict, Optional

try:
    import simplejson as json
except ImportError:
    import json

import requests

from optimade.models import DataType, EntryInfoResponse, SupportLevel
from optimade.validator.utils import (
    Client,
    test_case,
    print_failure,
    print_notify,
    print_success,
    print_warning,
    ResponseError,
    ValidatorEntryResponseOne,
    ValidatorEntryResponseMany,
    ValidatorResults,
)

from optimade.validator.config import VALIDATOR_CONFIG as CONF

VERSIONS_REGEXP = r".*/v[0-9]+(\.[0-9]+){,2}$"

__all__ = ("ImplementationValidator",)


class ImplementationValidator:
    """Class used to make a series of checks against a particular
    OPTIMADE implementation over HTTP.

    Uses the pydantic models in [`optimade.models`][optimade.models] to
    validate the response from the server and crawl through the
    available endpoints.

    Attributes:
        valid: whether or not the implementation was deemed valid, with
            `None` signifying that tests did not run.

    Caution:
        Only works for current version of the specification as defined
        by [`optimade.models`][optimade.models].

    """

    valid: Optional[bool]

    def __init__(  # pylint: disable=too-many-arguments
        self,
        client: Any = None,
        base_url: str = None,
        verbosity: int = 0,
        respond_json: bool = False,
        page_limit: int = 5,
        max_retries: int = 5,
        run_optional_tests: bool = True,
        fail_fast: bool = False,
        as_type: str = None,
        index: bool = False,
        minimal: bool = False,
        http_headers: Dict[str, str] = None,
    ):
        """Set up the tests to run, based on constants in this module
        for required endpoints.

        Arguments:
            client: A client that has a `.get()` method to obtain the
                response from the implementation. If `None`, then
                [`Client`][optimade.validator.utils.Client] will be used.
            base_url: The URL of the implementation to validate. Unless
                performing "as_type" validation, this should point to the
                base of the OPTIMADE implementation.
            verbosity: The verbosity of the output and logging as an integer
                (`0`: critical, `1`: warning, `2`: info, `3`: debug).
            respond_json: If `True`, print only a JSON representation of the
                results of validation to stdout.
            page_limit: The default page limit to apply to filters.
            max_retries: Argument is passed to the client for how many
                attempts to make for a request before failing.
            run_optional_tests: Whether to run the tests on optional
                OPTIMADE features.
            fail_fast: Whether to exit validation after the first failure
                of a mandatory test.
            as_type: An OPTIMADE entry or endpoint type to coerce the response
                from implementation into, e.g. "structures". Requires `base_url`
                to be pointed to the corresponding endpoint.
            index: Whether to validate the implementation as an index meta-database.
            minimal: Whether or not to run only a minimal test set.
            http_headers: Dictionary of additional headers to add to every request.

        """
        self.verbosity = verbosity
        self.max_retries = max_retries
        self.page_limit = page_limit
        self.index = index
        self.run_optional_tests = run_optional_tests
        self.fail_fast = fail_fast
        self.respond_json = respond_json
        self.minimal = minimal

        if as_type is None:
            self.as_type_cls = None
        elif self.index:
            if as_type not in CONF.response_classes_index:
                raise RuntimeError(
                    f"Provided as_type='{as_type}' not allowed for an Index meta-database."
                )
            self.as_type_cls = CONF.response_classes_index[as_type]
        elif as_type in ("structure", "reference"):
            self.as_type_cls = CONF.response_classes[f"{as_type}s/"]
        else:
            self.as_type_cls = CONF.response_classes[as_type]

        if client is None and base_url is None:
            raise RuntimeError(
                "Need at least a URL or a client to initialize validator."
            )
        if base_url and client:
            raise RuntimeError("Please specify at most one of base_url or client.")
        if client:
            self.client = client
            self.base_url = self.client.base_url
            # If a custom client has been provided, try to set custom headers if they have been specified,
            # but do not overwrite any existing attributes
            if http_headers:
                if not hasattr(self.client, "headers"):
                    self.client.headers = http_headers
                else:
                    print_warning(
                        f"Not using specified request headers {http_headers} with custom client {self.client}."
                    )
        else:
            while base_url.endswith("/"):
                base_url = base_url[:-1]
            self.base_url = base_url
            self.client = Client(
                base_url, max_retries=self.max_retries, headers=http_headers
            )

        self._setup_log()

        self._response_classes = (
            CONF.response_classes_index if self.index else CONF.response_classes
        )

        # some simple checks on base_url
        self.base_url_parsed = urllib.parse.urlparse(self.base_url)
        # only allow filters/endpoints if we are working in "as_type" mode
        if self.as_type_cls is None and self.base_url_parsed.query:
            raise SystemExit("Base URL not appropriate: should not contain a filter.")

        self.valid = None

        self._test_id_by_type = {}
        self._entry_info_by_type = {}

        self.results = ValidatorResults(verbosity=self.verbosity)

    def _setup_log(self):
        """Define stdout log based on given verbosity."""
        self._log = logging.getLogger("optimade").getChild("validator")
        self._log.handlers = []
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s | %(levelname)8s: %(message)s")
        )

        if not self.respond_json:
            self._log.addHandler(stdout_handler)
        else:
            self.verbosity = -1

        if self.verbosity == 0:
            self._log.setLevel(logging.CRITICAL)
        elif self.verbosity == 1:
            self._log.setLevel(logging.WARNING)
        elif self.verbosity == 2:
            self._log.setLevel(logging.INFO)
        elif self.verbosity > 0:
            self._log.setLevel(logging.DEBUG)

    def print_summary(self):
        """Print a summary of the results of validation."""
        if self.respond_json:
            print(json.dumps(dataclasses.asdict(self.results), indent=2))
            return

        if self.results.failure_messages:
            print("\n\nFAILURES")
            print("========\n")
            for message in self.results.failure_messages:
                print_failure(message[0])
                for line in message[1].split("\n"):
                    print_warning("\t" + line)

        if self.results.optional_failure_messages:
            print("\n\nOPTIONAL TEST FAILURES")
            print("======================\n")
            for message in self.results.optional_failure_messages:
                print_notify(message[0])
                for line in message[1].split("\n"):
                    print_warning("\t" + line)

        if self.results.internal_failure_messages:
            print("\n\nINTERNAL FAILURES")
            print("=================\n")
            print(
                "There were internal validator failures associated with this run.\n"
                "If this problem persists, please report it at:\n"
                "https://github.com/Materials-Consortia/optimade-python-tools/issues/new\n"
            )

            for message in self.results.internal_failure_messages:
                print_warning(message[0])
                for line in message[1].split("\n"):
                    print_warning("\t" + line)

        if self.valid or (not self.valid and not self.fail_fast):
            final_message = f"\n\nPassed {self.results.success_count} out of {self.results.success_count + self.results.failure_count + self.results.internal_failure_count} tests."
            if not self.valid:
                print_failure(final_message)
            else:
                print_success(final_message)

            if self.run_optional_tests and not self.fail_fast:
                print(
                    f"Additionally passed {self.results.optional_success_count} out of "
                    f"{self.results.optional_success_count + self.results.optional_failure_count} optional tests."
                )

    def validate_implementation(self):
        """Run all the test cases on the implementation, or the single type test,
        depending on what options were provided on initialiation.

        Sets the `self.valid` attribute to `True` or `False` depending on the
        outcome of the tests.

        Raises:
            RuntimeError: If it was not possible to start the validation process.

        """
        # If a single "as type" has been set, only run that test
        if self.as_type_cls is not None:
            self._log.debug(
                "Validating response of %s with model %s",
                self.base_url,
                self.as_type_cls,
            )
            self._test_as_type()
            self.valid = not bool(self.results.failure_count)
            self.print_summary()
            return

        # Test entire implementation
        if self.verbosity >= 0:
            print(f"Testing entire implementation at {self.base_url}")
        info_endp = CONF.info_endpoint
        self._log.debug("Testing base info endpoint of %s", info_endp)

        # Get and validate base info to find endpoints
        # If this is not possible, then exit at this stage
        base_info = self._test_info_or_links_endpoint(info_endp)
        if not base_info:
            self._log.critical(
                f"Unable to deserialize response from introspective {info_endp!r} endpoint. "
                "This is required for all further validation, so the validator will now exit."
            )
            # Set valid to False to ensure error code 1 is raised at CLI
            self.valid = False
            self.print_summary()
            return

        # Grab the provider prefix from base info and use it when looking for provider fields
        self.provider_prefix = None
        meta = base_info.get("meta", {})
        if meta.get("provider") is not None:
            self.provider_prefix = meta["provider"].get("prefix")

        # Set the response class for all `/info/entry` endpoints based on `/info` response
        self.available_json_endpoints, _ = self._get_available_endpoints(
            base_info, request=info_endp
        )
        for endp in self.available_json_endpoints:
            self._response_classes[f"{info_endp}/{endp}"] = EntryInfoResponse

        # Run some tests on the versions endpoint
        self._log.debug("Testing versions endpoint %s", CONF.versions_endpoint)
        self._test_versions_endpoint()
        self._test_bad_version_returns_553()

        # Test that entry info endpoints deserialize correctly
        # If they do not, the corresponding entry in _entry_info_by_type
        # is set to False, which must be checked for further validation
        for endp in self.available_json_endpoints:
            entry_info_endpoint = f"{info_endp}/{endp}"
            self._log.debug("Testing expected info endpoint %s", entry_info_endpoint)
            self._entry_info_by_type[endp] = self._test_info_or_links_endpoint(
                entry_info_endpoint
            )

        # Use the _entry_info_by_type to construct filters on the relevant endpoints
        if not self.minimal:
            for endp in self.available_json_endpoints:
                self._log.debug("Testing queries on JSON entry endpoint of %s", endp)
                self._recurse_through_endpoint(endp)

        # Test that the results from multi-entry-endpoints obey, e.g. page limits,
        # and that all entries can be deserialized with the patched models.
        # These methods also set the test_ids for each type of entry, which are validated
        # in the next loop.
        for endp in self.available_json_endpoints:
            self._log.debug("Testing multiple entry endpoint of %s", endp)
            self._test_multi_entry_endpoint(endp)

        # Test that the single IDs scraped earlier work with the single entry endpoint
        for endp in self.available_json_endpoints:
            self._log.debug("Testing single entry request of type %s", endp)
            self._test_single_entry_endpoint(endp)

        # Test that the links endpoint can be serialized correctly
        self._log.debug("Testing %s endpoint", CONF.links_endpoint)
        self._test_info_or_links_endpoint(CONF.links_endpoint)

        self.valid = not (
            self.results.failure_count or self.results.internal_failure_count
        )

        self.print_summary()

    @test_case
    def _recurse_through_endpoint(self, endp: str) -> Tuple[bool, str]:
        """For a given endpoint (`endp`), get the entry type
        and supported fields, testing that all mandatory fields
        are supported, then test queries on every property according
        to the reported type, with optionality decided by the
        specification-level support level for that field.

        Parameters:
            endp: Endpoint to be tested.

        Returns:
            `True` if endpoint passed the tests, and a string summary.

        """
        entry_info = self._entry_info_by_type.get(endp)

        if not entry_info:
            raise ResponseError(
                f"Unable to generate filters for endpoint {endp}: 'info/{endp}' response was malformed."
            )

        _impl_properties = self._check_entry_info(entry_info, endp)
        prop_list = list(_impl_properties.keys())

        self._check_response_fields(endp, prop_list)
        chosen_entry, _ = self._get_archetypal_entry(endp, prop_list)

        if not chosen_entry:
            return (
                None,
                f"Unable to generate filters for endpoint {endp}: no valid entries found.",
            )

        for prop in _impl_properties:
            # check support level of property
            prop_type = _impl_properties[prop]["type"]
            sortable = _impl_properties[prop]["sortable"]
            optional = (
                CONF.entry_schemas[endp].get(prop, {}).get("queryable")
                == SupportLevel.OPTIONAL
            )

            if optional and not self.run_optional_tests:
                continue

            self._construct_queries_for_property(
                prop,
                prop_type,
                sortable,
                endp,
                chosen_entry,
                request=f"; testing queries for {endp}->{prop}",
                optional=optional,
            )

        self._test_unknown_provider_property(endp)
        self._test_completely_unknown_property(endp)

        return True, f"successfully recursed through endpoint {endp}."

    @test_case
    def _test_completely_unknown_property(self, endp):
        request = f"{endp}?filter=crazyfield = 2"
        response, _ = self._get_endpoint(
            request,
            expected_status_code=400,
        )

        return True, "unknown field returned 400 Bad Request, as expected"

    @test_case
    def _test_unknown_provider_property(self, endp):

        dummy_provider_field = "_crazyprovider_field"

        request = f"{endp}?filter={dummy_provider_field}=2"
        response, _ = self._get_endpoint(
            request,
            multistage=True,
            request=request,
        )

        if response is not None:
            deserialized, _ = self._deserialize_response(
                response, CONF.response_classes[endp], request=request, multistage=True
            )

            return (
                True,
                "Unknown provider field was ignored when filtering, as expected",
            )

        raise ResponseError(
            "Failed to handle field from unknown provider; should return without affecting filter results"
        )

    def _check_entry_info(self, entry_info: Dict[str, Any], endp: str) -> List[str]:
        """Checks that `entry_info` contains all the required properties,
        and returns the property list for the endpoint.

        Parameters:
            entry_info: JSON representation of the response from the
                entry info endpoint.
            endp: The name of the entry endpoint.

        Returns:
            The list of property names supported by this implementation.

        """
        properties = entry_info.get("data", {}).get("properties", [])
        self._test_must_properties(
            properties, endp, request=f"{CONF.info_endpoint}/{endp}"
        )

        return properties

    @test_case
    def _test_must_properties(
        self, properties: List[str], endp: str
    ) -> Tuple[bool, str]:
        """Check that the entry info lists all properties with the "MUST"
        support level for this endpoint.

        Parameters:
            properties: The list of property names supported by the endpoint.
            endp: The endpoint.

        Returns:
            `True` if the properties were found, and a string summary.

        """
        must_props = set(
            prop
            for prop in CONF.entry_schemas.get(endp, {})
            if CONF.entry_schemas[endp].get(prop, {}).get("support")
            == SupportLevel.MUST
        )
        must_props_supported = set(prop for prop in properties if prop in must_props)
        missing = must_props - must_props_supported
        if len(missing) != 0:
            raise ResponseError(
                f"Some 'MUST' properties were missing from info/{endp}: {missing}"
            )

        return True, f"Found all required properties in entry info for endpoint {endp}"

    @test_case
    def _get_archetypal_entry(
        self, endp: str, properties: List[str]
    ) -> Tuple[Dict[str, Any], str]:
        """Get a random entry from the first page of results for this
        endpoint.

        Parameters:
            endp: The endpoint to query.

        Returns:
            The JSON representation of the chosen entry and the summary message.


        """
        response, message = self._get_endpoint(endp, multistage=True)

        if response:
            data = response.json().get("data", [])
            data_returned = len(data)
            if data_returned < 1:
                return (
                    None,
                    "Endpoint {endp!r} returned no entries, cannot get archetypal entry.",
                )

            response, message = self._get_endpoint(
                f"{endp}?page_offset={random.randint(0, data_returned-1)}&response_fields={','.join(properties)}",
                multistage=True,
            )
            if response:
                archetypal_entry = response.json()["data"][0]
                return (
                    archetypal_entry,
                    f"set archetypal entry for {endp} with ID {archetypal_entry['id']}.",
                )

        raise ResponseError(f"Failed to get archetypal entry. Details: {message}")

    @test_case
    def _check_response_fields(self, endp: str, fields: List[str]) -> Tuple[bool, str]:
        """Check that the response field query parameter is obeyed.

        Parameters:
            endp: The endpoint to query.
            fields: The known fields for this endpoint to test.

        Returns:
            Bool indicating success and a summary message.

        """

        subset_fields = random.sample(fields, min(len(fields) - 1, 3))
        test_query = f"{endp}?response_fields={','.join(subset_fields)}&page_limit=1"
        response, _ = self._get_endpoint(test_query, multistage=True)

        if response and len(response.json()["data"]) == 1:
            doc = response.json()["data"][0]
            expected_fields = set(subset_fields)
            expected_fields -= CONF.top_level_non_attribute_fields

            if "attributes" not in doc:
                raise ResponseError(
                    f"Entries are missing `attributes` key.\nReceived: {doc}"
                )

            returned_fields = set(sorted(list(doc.get("attributes", {}).keys())))
            returned_fields -= CONF.top_level_non_attribute_fields

            if expected_fields != returned_fields:
                raise ResponseError(
                    f"Response fields not obeyed by {endp!r}:\nExpected: {expected_fields}\nReturned: {returned_fields}"
                )

            return True, "Successfully limited response fields"

        return (
            None,
            f"Unable to test adherence to response fields as no entries were returned for endpoint {endp!r}.",
        )

    @test_case
    def _construct_queries_for_property(
        self,
        prop: str,
        prop_type: DataType,
        sortable: bool,
        endp: str,
        chosen_entry: Dict[str, Any],
    ) -> Tuple[Optional[bool], str]:
        """For the given property, property type and chose entry, this method
        runs a series of queries for each field in the entry, testing that the
        initial document is returned where expected.


        Parameters:
            prop: The property name.
            prop_type: The property type.
            sortable: Whether the implementation has indicated that the field is sortable.
            endp: The corresponding entry endpoint.
            chosen_entry: A JSON respresentation of the chosen entry that will be used to
                construct the filters.

        Returns:
            Boolean indicating success (`True`) or failure/irrelevance
            (`None`) and the string summary of the test case.

        """
        # Explicitly handle top level keys that do not have types in info
        if not chosen_entry:
            raise ResponseError(
                f"Chosen entry of endpoint '/{endp}' failed validation."
            )

        if prop == "type":
            if chosen_entry["type"] == endp:
                return True, f"Successfully validated {prop}"
            raise ResponseError(
                f"Chosen entry of endpoint '{endp}' had unexpected type {chosen_entry['type']!r}."
            )

        prop_type = (
            CONF.entry_schemas[endp].get(prop, {}).get("type")
            if prop_type is None
            else prop_type
        )

        if prop_type is None:
            raise ResponseError(
                f"Cannot validate queries on {prop!r} as field type was not reported in `/info/{endp}`"
            )

        # this is the case of a provider field
        if prop not in CONF.entry_schemas[endp]:
            if self.provider_prefix is None:
                raise ResponseError(
                    f"Found unknown field {prop!r} in `/info/{endp}` and no provider prefix was provided in `/info`"
                )
            elif not prop.startswith(f"_{self.provider_prefix}_"):
                raise ResponseError(
                    f"Found unknown field {prop!r} that did not start with provider prefix '_{self.provider_prefix}_'"
                )
            return (
                None,
                f"Found provider field {prop!r}, will not test queries as they are strictly optional.",
            )

        query_optional = (
            CONF.entry_schemas[endp].get(prop, {}).get("queryable")
            == SupportLevel.OPTIONAL
        )

        return self._construct_single_property_filters(
            prop, prop_type, sortable, endp, chosen_entry, query_optional
        )

    @staticmethod
    def _format_test_value(test_value: Any, prop_type: DataType, operator: str) -> str:
        """Formats the test value as a string according to the type of the property.

        Parameters:
            test_value: The value to format.
            prop_type: The OPTIMADE data type of the field.
            operator: The operator that will be applied to it.

        Returns:
            The value formatted as a string to use in an OPTIMADE filter.

        """
        if prop_type == DataType.LIST:
            if operator in ("HAS ALL", "HAS ANY"):
                _vals = sorted(set(test_value))
                if isinstance(test_value[0], str):
                    _vals = [f'"{val}"' for val in _vals]
                else:
                    _vals = [f"{val}" for val in _vals]
                _test_value = ",".join(_vals)
            else:
                if isinstance(test_value[0], str):
                    _test_value = f'"{test_value[0]}"'
                else:
                    _test_value = test_value[0]

        elif prop_type in (DataType.STRING, DataType.TIMESTAMP):
            _test_value = f'"{test_value}"'

        else:
            _test_value = test_value

        return _test_value

    def _construct_single_property_filters(
        self,
        prop: str,
        prop_type: DataType,
        sortable: bool,
        endp: str,
        chosen_entry: Dict[str, Any],
        query_optional: bool,
    ) -> Tuple[Optional[bool], str]:
        """This method constructs appropriate queries using all operators
        for a certain field and applies some tests:

        - inclusive operators return compatible entries, e.g. `>=` always returns
          at least the results of `=`.
        - exclusive operators never return contradictory entries, e.g.
          `nsites=1` never returns the same entries as `nsites!=1`, modulo
          pagination.

        Parameters:
            prop: The property name.
            prop_type: The property type.
            sortable: Whether the implementation has indicated that the field is sortable.
            endp: The corresponding entry endpoint.
            chosen_entry: A JSON respresentation of the chosen entry that will be used to
                construct the filters.
            query_optional: Whether to treat query success as optional.

        Returns:
            Boolean indicating success (`True`) or failure/irrelevance
            (`None`) and the string summary of the test case.

        """
        if prop == "id":
            test_value = chosen_entry.get("id")
        else:
            test_value = chosen_entry.get("attributes", {}).get(prop, "_missing")

        if test_value in ("_missing", None):
            support = CONF.entry_schemas[endp].get(prop, {}).get("support")
            queryable = CONF.entry_schemas[endp].get(prop, {}).get("queryable")
            submsg = "had no value" if test_value == "_missing" else "had `None` value"
            msg = (
                f"Chosen entry {submsg} for {prop!r} with support level {support} and queryability {queryable}, "
                f"so cannot construct test queries. This field should potentially be removed from the `/info/{endp}` endpoint response."
            )
            # None values are allowed for OPTIONAL and SHOULD, so we can just skip
            if support in (
                SupportLevel.OPTIONAL,
                SupportLevel.SHOULD,
            ):
                self._log.info(msg)
                return None, msg

            # Otherwise, None values are not allowed for MUST's, and entire missing fields are not allowed
            raise ResponseError(msg)

        using_fallback = False
        if prop_type == DataType.LIST:
            if not test_value:
                test_value = CONF.enum_fallback_values.get(endp, {}).get(prop)
                using_fallback = True

            if not test_value:
                msg = f"Not testing filters on field {prop} of type {prop_type} as no test value was found to use in filter."
                self._log.warning(msg)
                return None, msg
            if isinstance(test_value[0], dict) or isinstance(test_value[0], list):
                msg = f"Not testing filters on field {prop} of type {prop_type} with nested dictionary/list test value."
                self._log.warning(msg)
                return None, msg

            # Try to infer if the test value is a float from its string representation
            # and decide whether to do inclusive/exclusive query tests
            try:
                float(test_value[0])
                msg = f"Not testing filters on field {prop} of type {prop_type} containing float values."
                self._log.warning(msg)
                return None, msg
            except ValueError:
                pass

        if prop_type in (DataType.DICTIONARY,):
            msg = f"Not testing queries on field {prop} of type {prop_type}."
            self._log.warning(msg)
            return None, msg

        num_data_returned = {}

        inclusive_operators = CONF.inclusive_operators[prop_type]
        exclusive_operators = CONF.exclusive_operators[prop_type]

        for operator in inclusive_operators | exclusive_operators:
            # Need to pre-format list and string test values for the query
            _test_value = self._format_test_value(test_value, prop_type, operator)

            query = f"{prop} {operator} {_test_value}"
            request = f"{endp}?filter={query}"
            response, message = self._get_endpoint(
                request,
                multistage=True,
                optional=query_optional,
                expected_status_code=(200, 501),
            )

            if not response:
                if query_optional:
                    return (
                        None,
                        "Optional query {query!r} returned {reversed_response.status_code}.",
                    )
                raise ResponseError(
                    f"Unable to perform mandatory query {query!r}: responded with status code {response.status_code}"
                )

            response = response.json()

            if "meta" not in response or "more_data_available" not in response["meta"]:
                raise ResponseError(
                    f"Required field `meta->more_data_available` missing from response for {request}."
                )

            if not response["meta"]["more_data_available"]:
                num_data_returned[operator] = len(response["data"])
            else:
                num_data_returned[operator] = response["meta"].get("data_returned")

            num_response = num_data_returned[operator]

            # Numeric and string comparisons must work both ways...
            if prop_type in (
                DataType.STRING,
                DataType.INTEGER,
                DataType.FLOAT,
                DataType.TIMESTAMP,
            ) and operator not in (
                "CONTAINS",
                "STARTS",
                "STARTS WITH",
                "ENDS",
                "ENDS WITH",
            ):
                reversed_operator = operator.replace("<", ">")
                if "<" in operator:
                    reversed_operator = operator.replace("<", ">")
                elif ">" in operator:
                    reversed_operator = operator.replace(">", "<")

                # Don't try to reverse string comparison as it is ill-defined
                if prop_type == DataType.STRING and any(
                    comp in operator for comp in ("<", ">")
                ):
                    continue

                reversed_query = f"{_test_value} {reversed_operator} {prop}"
                reversed_request = f"{endp}?filter={reversed_query}"
                reversed_response, message = self._get_endpoint(
                    reversed_request,
                    multistage=True,
                    optional=query_optional,
                    expected_status_code=(200, 501),
                )

                if not reversed_response:
                    if query_optional:
                        return (
                            None,
                            "Optional query {query!r} returned {reversed_response.status_code}.",
                        )
                    raise ResponseError(
                        f"Unable to perform mandatory query {query!r}: responded with status code {reversed_response.status_code}"
                    )

                reversed_response = reversed_response.json()
                if (
                    "meta" not in reversed_response
                    or "more_data_available" not in reversed_response["meta"]
                ):
                    raise ResponseError(
                        f"Required field `meta->more_data_available` missing from response for {request}."
                    )

                if not reversed_response["meta"]["more_data_available"]:
                    num_reversed_response = len(reversed_response["data"])
                else:
                    num_reversed_response = reversed_response["meta"].get(
                        "data_returned"
                    )

                if num_response is not None and num_reversed_response is not None:
                    if reversed_response["meta"].get("data_returned") != response[
                        "meta"
                    ].get("data_returned"):
                        raise ResponseError(
                            f"Query {query} did not work both ways around: {reversed_query}, "
                            "returning different results each time."
                        )

                # check that the filter returned no entries that had a null or missing value for the filtered property
                if any(
                    entry["attributes"].get(prop, entry.get(prop, None)) is None
                    for entry in reversed_response.get("data", [])
                ):
                    raise ResponseError(
                        f"Filter {reversed_query!r} on field {prop!r} returned entries that had null or missing values for the field."
                    )

            excluded = operator in exclusive_operators
            # if we have all results on this page, check that the blessed ID is in the response
            if not response["meta"]["more_data_available"]:
                if excluded and (
                    chosen_entry["id"] in set(entry["id"] for entry in response["data"])
                ):
                    raise ResponseError(
                        f"Object {chosen_entry['id']} with value {test_value} was not excluded by {query}"
                    )

            # check that at least the archetypal structure was returned, unless we are using a fallback value
            if not excluded and not using_fallback:
                if (
                    num_data_returned[operator] is not None
                    and num_data_returned[operator] < 1
                ):
                    raise ResponseError(
                        f"Supposedly inclusive query '{query}' did not include original object ID {chosen_entry['id']} "
                        f"(with field '{prop} = {test_value}') potentially indicating a problem with filtering on this field."
                    )

            # check that the filter returned no entries that had a null or missing value for the filtered property
            if any(
                entry["attributes"].get(prop, entry.get(prop, None)) is None
                for entry in response.get("data", [])
            ):
                raise ResponseError(
                    f"Filter {query!r} on field {prop!r} returned entries that had null or missing values for the field."
                )

        if prop in CONF.unique_properties:
            if num_data_returned["="] is not None and num_data_returned["="] == 0:
                raise ResponseError(
                    f"Unable to filter field 'id' for equality, no data was returned for {query}."
                )
            if num_data_returned["="] is not None and num_data_returned["="] > 1:
                raise ResponseError(
                    f"Filter for an individual 'id' returned {num_data_returned['=']} results, when only 1 was expected."
                )

        return True, f"{prop} passed filter tests"

    def _test_info_or_links_endpoint(self, request_str: str) -> Union[bool, dict]:
        """Requests an info or links endpoint and attempts to deserialize
        the response.

        Parameters:
            request_str: The request to make, e.g. "links".

        Returns:
            `False` if the info response failed deserialization,
            otherwise returns the deserialized object.

        """
        response, _ = self._get_endpoint(request_str)
        if response:
            deserialized, _ = self._deserialize_response(
                response,
                self._response_classes[request_str],
                request=request_str,
            )
            if deserialized:
                return deserialized.dict()

        return False

    def _test_single_entry_endpoint(self, endp: str) -> None:
        """Requests and deserializes a single entry endpoint with the
        appropriate model.

        Parameters:
            request_str: The single entry request to make, e.g. "structures/id_1".

        """
        response_cls_name = endp + "/"
        if response_cls_name in self._response_classes:
            response_cls = self._response_classes[response_cls_name]
        else:
            self._log.warning(
                "Deserializing single entry response %s with generic response rather than defined endpoint.",
                endp,
            )
            response_cls = ValidatorEntryResponseOne

        response_fields = set()
        if endp in CONF.entry_schemas:
            response_fields = (
                set(CONF.entry_schemas[endp].keys())
                - CONF.top_level_non_attribute_fields
            )

        if endp in self._test_id_by_type:
            test_id = self._test_id_by_type[endp]
            request_str = f"{endp}/{test_id}"
            if response_fields:
                request_str += f"?response_fields={','.join(response_fields)}"
            response, _ = self._get_endpoint(request_str)
            if response:
                self._deserialize_response(response, response_cls, request=request_str)

    def _test_multi_entry_endpoint(self, endp: str) -> None:
        """Requests and deserializes a multi-entry endpoint with the
        appropriate model.

        TODO: deserialization is currently classed as an optional
        test until our models are robust to support levels.

        Parameters:
            request_str: The multi-entry request to make, e.g.,
                "structures?filter=nsites<10"

        """
        if endp in self._response_classes:
            response_cls = self._response_classes[endp]
        else:
            self._log.warning(
                "Deserializing multi entry response from %s with generic response rather than defined endpoint.",
                endp,
            )
            response_cls = ValidatorEntryResponseMany

        response_fields = set()
        if endp in CONF.entry_schemas:
            response_fields = (
                set(CONF.entry_schemas[endp].keys())
                - CONF.top_level_non_attribute_fields
            )

        request_str = f"{endp}?page_limit={self.page_limit}"

        if response_fields:
            request_str += f'&response_fields={",".join(response_fields)}'

        response, _ = self._get_endpoint(request_str)

        self._test_page_limit(response)

        deserialized, _ = self._deserialize_response(
            response, response_cls, request=request_str
        )

        self._get_single_id_from_multi_entry_endpoint(deserialized, request=request_str)
        if deserialized:
            self._test_data_available_matches_data_returned(
                deserialized, request=request_str
            )

    @test_case
    def _test_data_available_matches_data_returned(
        self, deserialized: Any
    ) -> Tuple[bool, str]:
        """In the case where no query is requested, `data_available`
        must equal `data_returned` in the meta response, which is tested
        here.

        Parameters:
            deserialized: The deserialized response to a multi-entry
                endpoint.

        Returns:
            `True` if successful, with a string summary.

        """
        if (
            deserialized.meta.data_available is None
            or deserialized.meta.data_returned is None
        ):
            return (
                None,
                "`meta->data_available` and/or `meta->data_returned` were not provided.",
            )

        if deserialized.meta.data_available != deserialized.meta.data_returned:
            raise ResponseError(
                "No query was performed, but `data_returned` != `data_available`."
            )

        return (
            True,
            "Meta response contained correct values for data_available and data_returned.",
        )

    def _test_versions_endpoint(self):
        """Requests and validate responses for the versions endpoint,
        which MUST exist for unversioned base URLs and MUST NOT exist
        for versioned base URLs.

        """

        # First, check that there is a versions endpoint in the appropriate place:
        # If passed a versioned URL, then strip that version from
        # the URL before looking for `/versions`.
        _old_base_url = self.base_url
        if re.match(VERSIONS_REGEXP, self.base_url_parsed.path) is not None:
            self.client.base_url = "/".join(self.client.base_url.split("/")[:-1])
            self.base_url = self.client.base_url

        response, _ = self._get_endpoint(
            CONF.versions_endpoint, expected_status_code=200
        )

        if response:
            self._test_versions_endpoint_content(
                response, request=CONF.versions_endpoint
            )

        # If passed a versioned URL, first reset the URL of the client to the
        # versioned one, then test that this versioned URL does NOT host a versions endpoint
        if re.match(VERSIONS_REGEXP, self.base_url_parsed.path) is not None:
            self.client.base_url = _old_base_url
            self.base_url = _old_base_url
            self._get_endpoint(CONF.versions_endpoint, expected_status_code=404)

    @test_case
    def _test_versions_endpoint_content(
        self, response: requests.Response
    ) -> Tuple[requests.Response, str]:
        """Checks that the response from the versions endpoint complies
        with the specification and that its 'Content-Type' header complies with
        [RFC 4180](https://tools.ietf.org/html/rfc4180.html).

        Parameters:
            response: The HTTP response from the versions endpoint.

        Raises:
            ResponseError: If any content checks fail.

        Returns:
            The successful HTTP response or `None`, and a summary string.

        """
        text_content = response.text.strip().split("\n")
        if text_content[0] != "version":
            raise ResponseError(
                f"First line of `/{CONF.versions_endpoint}` response must be 'version', not {text_content[0]!r}"
            )

        if len(text_content) <= 1:
            raise ResponseError(
                f"No version numbers found in `/{CONF.versions_endpoint}` response, only {text_content}"
            )

        for version in text_content[1:]:
            try:
                int(version)
            except ValueError:
                raise ResponseError(
                    f"Version numbers reported by `/{CONF.versions_endpoint}` must be integers specifying the major version, not {text_content}."
                )

        content_type = response.headers.get("content-type")
        if not content_type:
            raise ResponseError(
                "Missing 'Content-Type' in response header from `/versions`."
            )

        content_type = [_.replace(" ", "") for _ in content_type.split(";")]

        self._test_versions_headers(
            content_type,
            ("text/csv", "text/plain"),
            optional=True,
            request=CONF.versions_endpoint,
        )
        self._test_versions_headers(
            content_type,
            "header=present",
            optional=True,
            request=CONF.versions_endpoint,
        )

        return response, "`/versions` endpoint responded correctly."

    @test_case
    def _test_versions_headers(
        self,
        content_type: Dict[str, Any],
        expected_parameter: Union[str, List[str]],
    ) -> Tuple[Dict[str, Any], str]:
        """Tests that the `Content-Type` field of the `/versions` header contains
        the passed parameter.

        Arguments:
            content_type: The 'Content-Type' field from the response of the `/versions` endpoint.
            expected_paramter: A substring or list of substrings that are expected in
                the Content-Type of the response. If multiple strings are passed, they will
                be treated as possible alternatives to one another.

        Raises:
            ResponseError: If the expected 'Content-Type' parameter is missing.

        Returns:
            The HTTP response headers and a summary string.

        """

        if isinstance(expected_parameter, str):
            expected_parameter = [expected_parameter]

        if not any(param in content_type for param in expected_parameter):
            raise ResponseError(
                f"Incorrect 'Content-Type' header {';'.join(content_type)!r}.\n"
                f"Missing at least one expected parameter(s): {expected_parameter!r}"
            )

        return (
            content_type,
            f"`/versions` response had one of the expected Content-Type parameters {expected_parameter}.",
        )

    def _test_as_type(self) -> None:
        """Tests that the base URL of the validator (i.e. with no
        additional path added) validates with the model selected.

        """
        response, _ = self._get_endpoint("")
        if response:
            self._log.debug("Deserialzing response as type %s", self.as_type_cls)
            self._deserialize_response(response, self.as_type_cls)

    def _test_bad_version_returns_553(self) -> None:
        """Tests that a garbage version number responds with a 553
        error code.

        """
        expected_status_code = 553
        if re.match(VERSIONS_REGEXP, self.base_url_parsed.path) is not None:
            expected_status_code = [404, 400]

        self._get_endpoint(
            "v123123", expected_status_code=expected_status_code, optional=True
        )

    @test_case
    def _test_page_limit(
        self, response: requests.models.Response, check_next_link: int = 5
    ) -> Tuple[Optional[bool], str]:
        """Test that a multi-entry endpoint obeys the page limit by
        following pagination links up to a depth of `check_next_link`.

        Parameters:
            response: The response to test for page limit
                compliance.
            check_next_link: Maximum recursion depth for following
                pagination links.

        Returns:
            `True` if the test was successful and `None` if not, with a
            string summary.

        """
        try:
            response = response.json()
        except (AttributeError, json.JSONDecodeError):
            raise ResponseError("Unable to test endpoint `page_limit` parameter.")

        try:
            num_entries = len(response["data"])
        except (KeyError, TypeError):
            raise ResponseError(
                "Response under `data` field was missing or had wrong type."
            )

        if num_entries > self.page_limit:
            raise ResponseError(
                f"Endpoint did not obey page limit: {num_entries} entries vs {self.page_limit} limit"
            )

        try:
            more_data_available = response["meta"]["more_data_available"]
        except KeyError:
            raise ResponseError("Field `meta->more_data_available` was missing.")

        if more_data_available and check_next_link:
            try:
                next_link = response["links"]["next"]
                if isinstance(next_link, dict):
                    next_link = next_link["href"]
            except KeyError:
                raise ResponseError(
                    "Endpoint suggested more data was available but provided no valid links->next link."
                )

            if not isinstance(next_link, str):
                raise ResponseError(
                    f"Unable to parse links->next {next_link!r} as a link."
                )

            self._log.debug("Following pagination link to %r.", next_link)
            next_response, _ = self._get_endpoint(next_link)
            if not next_response:
                raise ResponseError(
                    f"Error when testing pagination: the response from `links->next` {next_link!r} failed the previous test."
                )

            check_next_link = bool(check_next_link - 1)
            self._test_page_limit(
                next_response,
                check_next_link=check_next_link,
                multistage=check_next_link,
            )

        return (
            True,
            f"Endpoint obeyed page limit of {self.page_limit} by returning {num_entries} entries.",
        )

    @test_case
    def _get_single_id_from_multi_entry_endpoint(self, deserialized):
        """Scrape an ID from the multi-entry endpoint to use as query
        for single entry endpoint.

        """
        if deserialized and deserialized.data:
            self._test_id_by_type[deserialized.data[0].type] = deserialized.data[0].id
            self._log.debug(
                "Set type %s test ID to %s",
                deserialized.data[0].type,
                deserialized.data[0].id,
            )
        else:
            return (
                None,
                "No entries found under endpoint to scrape ID from. "
                "This may be caused by previous errors, if e.g. the endpoint failed deserialization.",
            )
        return (
            self._test_id_by_type[deserialized.data[0].type],
            f"successfully scraped test ID from {deserialized.data[0].type} endpoint",
        )

    @test_case
    def _deserialize_response(
        self, response: requests.models.Response, response_cls: Any, request: str = None
    ) -> Tuple[Any, str]:
        """Try to create the appropriate pydantic model from the response.

        Parameters:
            response: The response to try to deserialize.
            response_cls: The class to use for deserialization.
            request: Optional string that will be displayed as the attempted
                request in the validator output.

        Returns:
            The deserialized object (or `None` if unsuccessful) and a
                human-readable summary

        """
        if not response:
            raise ResponseError("Request failed")
        try:
            json_response = response.json()
        except json.JSONDecodeError:
            raise ResponseError(
                f"Unable to decode response as JSON. Response: {response}"
            )

        self._log.debug(
            f"Deserializing {json.dumps(json_response, indent=2)} as model {response_cls}"
        )

        return (
            response_cls(**json_response),
            "deserialized correctly as object of type {}".format(response_cls),
        )

    @test_case
    def _get_available_endpoints(
        self, base_info: Union[Any, Dict[str, Any]]
    ) -> Tuple[Optional[List[str]], str]:
        """Tries to get `entry_types_by_format` from base info response
        even if it could not be deserialized.

        Parameters:
            base_info: Either the unvalidated JSON representation of the
                base info, or the deserialized object.

        Returns:
            The list of JSON entry endpoints (or `None` if unavailable)
            and a string summary.

        """
        for _ in [0]:
            try:
                available_json_entry_endpoints = base_info["data"]["attributes"][
                    "entry_types_by_format"
                ]["json"]
                break
            except (KeyError, TypeError):
                raise ResponseError(
                    "Unable to get entry_types_by_format from unserializable base info response {}.".format(
                        base_info
                    )
                )
        else:
            raise ResponseError(
                "Unable to find any JSON entry types in entry_types_by_format"
            )

        if self.index and available_json_entry_endpoints != []:
            raise ResponseError(
                "No entry endpoint are allowed for an Index meta-database"
            )

        for non_entry_endpoint in CONF.non_entry_endpoints:
            if non_entry_endpoint in available_json_entry_endpoints:
                raise ResponseError(
                    f'Illegal entry "{non_entry_endpoint}" was found in entry_types_by_format"'
                )

        # Filter out custom extension endpoints that are not covered in the specification
        available_json_entry_endpoints = [
            endp
            for endp in available_json_entry_endpoints
            if endp in CONF.entry_endpoints
        ]

        return (
            available_json_entry_endpoints,
            "successfully found available entry types in baseinfo",
        )

    @test_case
    def _get_endpoint(
        self, request_str: str, expected_status_code: Union[List[int], int] = 200
    ) -> Tuple[Optional[requests.Response], str]:
        """Gets the response from the endpoint specified by `request_str`.
        function is wrapped by the `test_case` decorator

        Parameters:
            request_str: The request to make to the client.
            expected_status_code: If the request responds with a different
                status code to this one, raise a ResponseError.

        Returns:
            The response to the request (if successful) or `None`, plus
            a string summary.

        """
        request_str = request_str.replace("\n", "")
        response = self.client.get(request_str)

        if isinstance(expected_status_code, int):
            expected_status_code = [expected_status_code]

        if response.status_code not in expected_status_code:
            message = f"Request to '{request_str}' returned HTTP code {response.status_code} and not the allowed {expected_status_code}."
            message += "\nAdditional details:"
            try:
                for error in response.json().get("errors", []):
                    message += f'\n  {error.get("title", "N/A")}: {error.get("detail", "N/A")} ({error.get("source", {}).get("pointer", "N/A")})'
            except json.JSONDecodeError:
                message += f"\n  Could not parse response as JSON. Content type was {response.headers.get('content-type')!r}."
            raise ResponseError(message)

        return response, f"received expected response: {response}."
