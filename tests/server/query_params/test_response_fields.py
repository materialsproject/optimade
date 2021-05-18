"""Make sure response_fields is handled correctly"""


def test_required_fields_links(check_required_fields_response):
    """Certain fields are REQUIRED, no matter the value of `response_fields`"""
    endpoint = "links"
    illegal_top_level_field = "relationships"
    non_used_top_level_fields = {"links"}
    non_used_top_level_fields.add(illegal_top_level_field)
    expected_fields = {"homepage", "base_url", "link_type"}
    check_required_fields_response(endpoint, non_used_top_level_fields, expected_fields)


def test_required_fields_references(check_required_fields_response):
    """Certain fields are REQUIRED, no matter the value of `response_fields`"""
    endpoint = "references"
    non_used_top_level_fields = {"links", "relationships"}
    expected_fields = {"year", "journal"}
    check_required_fields_response(endpoint, non_used_top_level_fields, expected_fields)


def test_required_fields_structures(check_required_fields_response):
    """Certain fields are REQUIRED, no matter the value of `response_fields`"""
    endpoint = "structures"
    non_used_top_level_fields = {"links"}
    expected_fields = {"elements", "nelements"}
    check_required_fields_response(endpoint, non_used_top_level_fields, expected_fields)


def test_unknown_field_structures(
    check_required_fields_response, check_error_response, check_response, structures
):
    """Check that unknown fields are returned as `null` in entries."""
    endpoint = "structures"
    non_used_top_level_fields = {"links"}

    expected_fields = {"_optimade_field"}
    check_required_fields_response(endpoint, non_used_top_level_fields, expected_fields)

    expected_fields = {"optimade_field"}
    check_error_response(
        request=f"/{endpoint}?response_fields={','.join(expected_fields)}",
        expected_status=400,
        expected_title="Bad Request",
        expected_detail="Unrecognised OPTIMADE field(s) in requested `response_fields`: {'optimade_field'}.",
    )

    expected_fields = {"_exmpl_optimade_field"}
    expected_ids = [doc["task_id"] for doc in structures]
    expected_warnings = [
        {
            "title": "UnknownProviderProperty",
            "detail": "Unrecognised field(s) for this provider requested in `response_fields`: {'_exmpl_optimade_field'}.",
        }
    ]
    check_response(
        request=f"/{endpoint}?response_fields={','.join(expected_fields)}",
        expected_ids=expected_ids,
        expected_warnings=expected_warnings,
    )

    expected_fields = {"_exmpl123_optimade_field"}
    expected_ids = [doc["task_id"] for doc in structures]
    check_response(
        request=f"/{endpoint}?response_fields={','.join(expected_fields)}",
        expected_ids=expected_ids,
    )
