from optimade.models import (
    StructureResponseMany,
    StructureResponseOne,
    ReferenceResource,
)

from ..utils import RegularEndpointTests


class TestStructuresEndpoint(RegularEndpointTests):
    """Tests for /structures"""

    request_str = "/structures"
    response_cls = StructureResponseMany

    def test_structures_endpoint_data(self):
        """Check known properties/attributes for successful response"""
        assert "meta" in self.json_response
        assert self.json_response["meta"]["data_available"] == 17
        assert not self.json_response["meta"]["more_data_available"]
        assert "data" in self.json_response
        assert (
            len(self.json_response["data"])
            == self.json_response["meta"]["data_available"]
        )

    def test_get_next_responses(self, get_good_response):
        """Check pagination"""
        total_data = self.json_response["meta"]["data_available"]
        page_limit = 5

        json_response = get_good_response(
            self.request_str + f"?page_limit={page_limit}"
        )

        cursor = json_response["data"].copy()
        assert json_response["meta"]["more_data_available"]
        more_data_available = True
        next_request = json_response["links"]["next"]

        while more_data_available:
            next_response = get_good_response(next_request)
            next_request = next_response["links"]["next"]
            cursor.extend(next_response["data"])
            more_data_available = next_response["meta"]["more_data_available"]
            if more_data_available:
                assert len(next_response["data"]) == page_limit
            else:
                assert len(next_response["data"]) == total_data % page_limit

        assert len(cursor) == total_data


class TestSingleStructureEndpoint(RegularEndpointTests):
    """Tests for /structures/<entry_id>"""

    test_id = "mpf_1"
    request_str = f"/structures/{test_id}"
    response_cls = StructureResponseOne

    def test_structures_endpoint_data(self):
        """Check known properties/attributes for successful response"""
        assert "data" in self.json_response
        assert self.json_response["data"]["id"] == self.test_id
        assert self.json_response["data"]["type"] == "structures"
        assert "attributes" in self.json_response["data"]
        assert "_exmpl_chemsys" in self.json_response["data"]["attributes"]


class TestMissingSingleStructureEndpoint(RegularEndpointTests):
    """Tests for /structures/<entry_id> for unknown <entry_id>"""

    test_id = "mpf_random_string_that_is_not_in_test_data"
    request_str = f"/structures/{test_id}"
    response_cls = StructureResponseOne

    def test_structures_endpoint_data(self):
        """Check known properties/attributes for successful response"""
        assert "data" in self.json_response
        assert "meta" in self.json_response
        assert self.json_response["data"] is None
        assert self.json_response["meta"]["data_returned"] == 0
        assert not self.json_response["meta"]["more_data_available"]


class TestSingleStructureWithRelationships(RegularEndpointTests):
    """Tests for /structures/<entry_id>, where <entry_id> has relationships"""

    test_id = "mpf_1"
    request_str = f"/structures/{test_id}"
    response_cls = StructureResponseOne

    def test_structures_endpoint_data(self):
        """Check known properties/attributes for successful response"""
        assert "data" in self.json_response
        assert self.json_response["data"]["id"] == self.test_id
        assert self.json_response["data"]["type"] == "structures"
        assert "attributes" in self.json_response["data"]
        assert "relationships" in self.json_response["data"]
        assert self.json_response["data"]["relationships"] == {
            "references": {"data": [{"type": "references", "id": "dijkstra1968"}]}
        }
        assert "included" in self.json_response
        assert len(
            self.json_response["data"]["relationships"]["references"]["data"]
        ) == len(self.json_response["included"])

        ReferenceResource(**self.json_response["included"][0])


class TestMultiStructureWithSharedRelationships(RegularEndpointTests):
    """Tests for /structures for entries with shared relationships"""

    request_str = '/structures?filter=id="mpf_1" OR id="mpf_2"'
    response_cls = StructureResponseMany

    def test_structures_endpoint_data(self):
        """Check known properties/attributes for successful response"""
        # mpf_1 and mpf_2 both contain the same reference relationship, so response should not duplicate it
        assert "data" in self.json_response
        assert len(self.json_response["data"]) == 2
        assert "included" in self.json_response
        assert len(self.json_response["included"]) == 1


class TestMultiStructureWithRelationships(RegularEndpointTests):
    """Tests for /structures for mixed entries with and without relationships"""

    request_str = '/structures?filter=id="mpf_1" OR id="mpf_23"'
    response_cls = StructureResponseMany

    def test_structures_endpoint_data(self):
        """Check known properties/attributes for successful response"""
        # mpf_23 contains no relationships, which shouldn't break anything
        assert "data" in self.json_response
        assert len(self.json_response["data"]) == 2
        assert "included" in self.json_response
        assert len(self.json_response["included"]) == 1


class TestMultiStructureWithOverlappingRelationships(RegularEndpointTests):
    """Tests for /structures with entries with overlapping relationships

    One entry has multiple relationships, another entry has other relationships,
    some of these relationships overlap between the entries, others don't.
    """

    request_str = '/structures?filter=id="mpf_1" OR id="mpf_3"'
    response_cls = StructureResponseMany

    def test_structures_endpoint_data(self):
        """Check known properties/attributes for successful response"""
        assert "data" in self.json_response
        assert len(self.json_response["data"]) == 2
        assert "included" in self.json_response
        assert len(self.json_response["included"]) == 2


class TestStructuresWithNullFieldsDoNotMatchNegatedFilters(RegularEndpointTests):
    """Tests that structures with e.g., `'assemblies':null` do not get
    returned for negated queries like `filter=assemblies != 1`, as mandated
    by the specification.

    """

    request_str = "/structures?filter=assemblies != 1"
    response_cls = StructureResponseMany

    def test_structures_endpoint_data(self):
        """Check that no structures are returned."""
        assert len(self.json_response["data"]) == 0


class TestStructuresWithNullFieldsMatchUnknownFilter(RegularEndpointTests):
    """Tests that structures with e.g., `'assemblies':null` do get
    returned for queries testing for "UNKNOWN" fields.

    """

    request_str = "/structures?filter=assemblies IS UNKNOWN"
    response_cls = StructureResponseMany

    def test_structures_endpoint_data(self):
        """Check that all structures are returned."""
        assert len(self.json_response["data"]) == 17


class TestStructuresWithUnknownResponseFields(RegularEndpointTests):
    """Tests that structures with e.g., `'assemblies':null` do get
    returned for queries testing for "UNKNOWN" fields.

    """

    request_str = "/structures?filter=assemblies IS UNKNOWN&response_fields=assemblies,_other_provider_field,chemical_formula_anonymous"
    response_cls = StructureResponseMany

    def test_structures_endpoint_data(self):
        """Check that all structures are returned."""
        assert len(self.json_response["data"]) == 17
        keys = ("_other_provider_field", "assemblies", "chemical_formula_anonymous")
        for key in keys:
            assert all(key in doc["attributes"] for doc in self.json_response["data"])
        assert all(
            doc["attributes"]["_other_provider_field"] is None
            for doc in self.json_response["data"]
        )
        assert all(
            len(doc["attributes"]) == len(keys) for doc in self.json_response["data"]
        )
