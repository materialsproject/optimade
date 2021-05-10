"""Make sure filters are handled correctly"""
import pytest
from optimade.server.config import CONFIG, SupportedBackend


@pytest.mark.xfail(
    CONFIG.database_backend == SupportedBackend.ELASTIC,
    reason="Elasticsearch does not support queries on custom fields without configuration.",
)
def test_custom_field(check_response):
    request = '/structures?filter=_exmpl_chemsys="Ac"'
    expected_ids = ["mpf_1"]
    check_response(request, expected_ids)


def test_id(check_response):
    request = '/structures?filter=id="mpf_2"'
    expected_ids = ["mpf_2"]
    check_response(request, expected_ids)


def test_geq(check_response):
    request = "/structures?filter=nelements>=9"
    expected_ids = ["mpf_3819"]
    check_response(request, expected_ids)


def test_gt(check_response):
    request = "/structures?filter=nelements>8"
    expected_ids = ["mpf_3819"]
    check_response(request, expected_ids)


def test_rhs_comparison(check_response):
    request = "/structures?filter=8<nelements"
    expected_ids = ["mpf_3819"]
    check_response(request, expected_ids)


def test_gt_none(check_response):
    request = "/structures?filter=nelements>9"
    expected_ids = []
    check_response(request, expected_ids)


def test_list_has(check_response):
    request = '/structures?filter=elements HAS "Ti"'
    expected_ids = ["mpf_3803", "mpf_3819"]
    check_response(request, expected_ids)


def test_page_limit(check_response):
    request = '/structures?filter=elements HAS "Ac"&page_limit=2'
    expected_ids = ["mpf_1", "mpf_110"]
    expected_return = 6
    check_response(request, expected_ids=expected_ids, expected_return=expected_return)

    request = '/structures?page_limit=2&filter=elements HAS "Ac"'
    expected_ids = ["mpf_1", "mpf_110"]
    expected_return = 6
    check_response(request, expected_ids=expected_ids, expected_return=expected_return)


def test_page_limit_max(check_error_response):

    request = f"/structures?page_limit={CONFIG.page_limit_max + 1}"
    check_error_response(
        request,
        expected_status=403,
        expected_title="Forbidden",
        expected_detail=f"Max allowed page_limit is {CONFIG.page_limit_max}, you requested {CONFIG.page_limit_max + 1}",
    )


def test_value_list_operator(check_error_response):
    request = "/structures?filter=dimension_types HAS < 1"
    if CONFIG.database_backend == SupportedBackend.ELASTIC:
        expected_detail = "Unrecognised operation HAS <."
    else:
        expected_detail = "set_op_rhs not implemented for use with OPERATOR. Given: [Token('HAS', 'HAS'), Token('OPERATOR', '<'), 1]"
    check_error_response(
        request,
        expected_status=501,
        expected_title="NotImplementedError",
        expected_detail=expected_detail,
    )


def test_has_any_operator(check_response, check_error_response):
    request = "/structures?filter=dimension_types HAS ANY > 1"
    if CONFIG.database_backend == SupportedBackend.ELASTIC:
        check_response(request, [])
    else:
        check_error_response(
            request,
            expected_status=501,
            expected_title="NotImplementedError",
            expected_detail="OPERATOR > inside value_list [Token('OPERATOR', '>'), 1] not implemented.",
        )


def test_list_has_all(check_response):
    request = '/structures?filter=elements HAS ALL "Ba","F","H","Mn","O","Re","Si"'
    expected_ids = ["mpf_3819"]
    check_response(request, expected_ids)

    request = '/structures?filter=elements HAS ALL "Re","Ti"'
    expected_ids = ["mpf_3819"]
    check_response(request, expected_ids)


def test_list_has_any(check_response):
    request = '/structures?filter=elements HAS ANY "Re","Ti"'
    expected_ids = ["mpf_3819", "mpf_3803"]
    check_response(request, expected_ids)


def test_list_length_basic(check_response):
    request = "/structures?filter=elements LENGTH = 9"
    expected_ids = ["mpf_3819"]
    check_response(request, expected_ids)

    request = "/structures?filter=elements LENGTH 9"
    check_response(request, expected_ids)


def test_list_length_comparisons_aliased(check_response, check_error_response):
    """Test whether list length comparisons work on fields that have
    defined length aliases.

    """

    request = "/structures?filter=elements LENGTH >= 9"
    expected_ids = ["mpf_3819"]
    check_response(request, expected_ids)

    request = "/structures?filter=cartesian_site_positions LENGTH > 43"
    expected_ids = sorted(["mpf_3803", "mpf_3819", "mpf_551"])
    check_response(request, expected_ids, expected_as_is=True)

    request = "/structures?filter=species_at_sites LENGTH > 43"
    expected_ids = sorted(["mpf_551", "mpf_3803", "mpf_3819"])
    check_response(request, expected_ids, expected_as_is=True)

    request = "/structures?filter=nsites LENGTH > 43"
    expected_ids = []
    if CONFIG.database_backend == SupportedBackend.ELASTIC:
        check_error_response(
            request,
            expected_status=501,
            expected_title="NotImplementedError",
            expected_detail="LENGTH is not supported for 'nsites'",
        )
    else:
        check_response(request, expected_ids)


@pytest.mark.xfail(
    CONFIG.database_backend == SupportedBackend.ELASTIC,
    reason="Elasticsearch does not support length queries on fields with no defined length alias.",
)
def test_list_length_comparisons_unaliased(check_response, check_error_response):
    """Test whether list length comparisons work on fields that have no
    defined length aliases.

    """
    request = "/structures?filter=structure_features LENGTH > 0"
    expected_ids = []
    check_response(request, expected_ids)

    request = "/structures?filter=structure_features LENGTH != 0"
    error_detail = "Operator != not implemented for LENGTH filter."
    check_error_response(
        request,
        expected_status=501,
        expected_title="NotImplementedError",
        expected_detail=error_detail,
    )


@pytest.mark.xfail(
    CONFIG.database_backend == SupportedBackend.ELASTIC,
    reason="Elasticsearch does not support HAS ONLY queries.",
)
def test_list_has_only(check_response):
    """Test HAS ONLY query on elements."""
    request = '/structures?filter=elements HAS ONLY "Ac", "Mg"'
    expected_ids = ["mpf_23"]
    check_response(request, expected_ids)

    request = '/structures?filter=elements HAS ONLY "Ac"'
    expected_ids = ["mpf_1"]
    check_response(request, expected_ids)

    request = '/structures?filter=elements HAS ONLY "Ac" AND nelements IS KNOWN'
    expected_ids = ["mpf_1"]
    check_response(request, expected_ids)


def test_list_correlated(check_error_response):
    request = '/structures?filter=elements:elements_ratios HAS "Ag":"0.2"'
    check_error_response(
        request,
        expected_status=501,
        expected_title="NotImplementedError",
        expected_detail="Correlated list queries are not supported.",
    )
    # expected_ids = ["mpf_259"]
    # check_response(request, expected_ids)


def test_timestamp_query(check_response):
    from optimade.server.warnings import TimestampNotRFCCompliant

    request = '/structures?filter=last_modified="2019-06-08T05:13:37.331Z"&page_limit=5'
    expected_ids = ["mpf_1", "mpf_2", "mpf_3"]
    if CONFIG.database_backend == SupportedBackend.ELASTIC:
        check_response(request, expected_ids, expected_as_is=True)
    else:
        with pytest.warns(TimestampNotRFCCompliant):
            check_response(request, expected_ids, expected_as_is=True)

    request = '/structures?filter=last_modified<"2019-06-08T05:13:37.331Z"&page_limit=5'
    expected_ids = ["mpf_3819"]
    if CONFIG.database_backend == SupportedBackend.ELASTIC:
        check_response(request, expected_ids, expected_as_is=True)
    else:
        with pytest.warns(TimestampNotRFCCompliant):
            check_response(request, expected_ids, expected_as_is=True)

    request = '/structures?filter=last_modified="2018-06-08T05:13:37.945Z"&page_limit=5'
    expected_ids = ["mpf_3819"]
    if CONFIG.database_backend == SupportedBackend.ELASTIC:
        check_response(request, expected_ids, expected_as_is=True)
    else:
        with pytest.warns(TimestampNotRFCCompliant):
            check_response(request, expected_ids, expected_as_is=True)

    request = '/structures?filter=last_modified>"2018-06-08T05:13:37.945Z" AND last_modified<="2019-06-08T05:13:37.331Z"&page_limit=5'
    expected_ids = ["mpf_1", "mpf_2", "mpf_3"]
    if CONFIG.database_backend == SupportedBackend.ELASTIC:
        check_response(request, expected_ids, expected_as_is=True)
    else:
        with pytest.warns(TimestampNotRFCCompliant):
            check_response(request, expected_ids, expected_as_is=True)


def test_is_known(check_response):
    request = "/structures?filter=nsites IS KNOWN AND nsites>=44"
    expected_ids = sorted(["mpf_551", "mpf_3803", "mpf_3819"])
    check_response(request, expected_ids, expected_as_is=True)

    request = "/structures?filter=lattice_vectors IS KNOWN AND nsites>=44"
    expected_ids = sorted(["mpf_551", "mpf_3803", "mpf_3819"])
    check_response(request, expected_ids, expected_as_is=True)


def test_aliased_is_known(check_response):
    request = "/structures?filter=id IS KNOWN AND nsites>=44"
    expected_ids = sorted(["mpf_551", "mpf_3803", "mpf_3819"])
    check_response(request, expected_ids, expected_as_is=True)

    request = "/structures?filter=chemical_formula_reduced IS KNOWN AND nsites>=44"
    expected_ids = sorted(["mpf_551", "mpf_3803", "mpf_3819"])
    check_response(request, expected_ids, expected_as_is=True)

    request = "/structures?filter=chemical_formula_descriptive IS KNOWN AND nsites>=44"
    expected_ids = sorted(["mpf_551", "mpf_3803", "mpf_3819"])
    check_response(request, expected_ids, expected_as_is=True)


def test_aliased_fields(check_response):
    request = '/structures?filter=chemical_formula_anonymous="A"'
    expected_ids = ["mpf_1", "mpf_200"]
    check_response(request, expected_ids, expected_as_is=True)

    request = '/structures?filter=chemical_formula_anonymous CONTAINS "A2BC"'
    expected_ids = ["mpf_110", "mpf_2", "mpf_3"]
    check_response(request, expected_ids, expected_as_is=True)


def test_string_contains(check_response):
    request = '/structures?filter=chemical_formula_descriptive CONTAINS "c2Ag"'
    expected_ids = ["mpf_3", "mpf_2"]
    check_response(request, expected_ids)


def test_string_start(check_response):
    request = '/structures?filter=chemical_formula_descriptive STARTS WITH "Ag2CClN"'
    expected_ids = ["mpf_259"]
    check_response(request, expected_ids)


def test_string_end(check_response):
    request = '/structures?filter=chemical_formula_descriptive ENDS WITH "ClNO4S"'
    expected_ids = ["mpf_259"]
    check_response(request, expected_ids)


def test_list_has_and(check_response):
    request = '/structures?filter=elements HAS "Ac" AND nelements=1'
    expected_ids = ["mpf_1"]
    check_response(request, expected_ids)


def test_awkward_not_queries(check_response, client):
    """Test an awkward query from the spec examples. It should return all but 2 structures
    in the test data. The test is done in three parts:

        - first query the individual expressions that make up the OR,
        - then do an empty query to get all IDs
        - then negate the expressions and ensure that all IDs are returned except
            those from the first queries.

    """
    expected_ids = ["mpf_3819"]
    request = (
        '/structures?filter=chemical_formula_descriptive="Ba2FHMnNaO26Re2Si8Ti2" AND '
        'chemical_formula_anonymous = "A26B8C2D2E2FGHI" '
    )
    check_response(request, expected_ids)

    expected_ids = ["mpf_2"]
    request = (
        '/structures?filter=chemical_formula_anonymous = "A2BC" AND '
        'NOT chemical_formula_descriptive = "Ac2AgPb" '
    )
    check_response(request, expected_ids)

    request = "/structures"
    unexpected_ids = ["mpf_3819", "mpf_2"]
    expected_ids = [
        structure["id"]
        for structure in client.get(request).json()["data"]
        if structure["id"] not in unexpected_ids
    ]

    request = (
        "/structures?filter="
        "NOT ( "
        'chemical_formula_descriptive = "Ba2FHMnNaO26Re2Si8Ti2" AND '
        'chemical_formula_anonymous = "A26B8C2D2E2FGHI" OR '
        'chemical_formula_anonymous = "A2BC" AND '
        'NOT chemical_formula_descriptive = "Ac2AgPb" '
        ")"
    )
    check_response(request, expected_ids, expected_as_is=True)


def test_not_or_and_precedence(check_response):
    request = '/structures?filter=NOT elements HAS "Ac" AND nelements=1'
    expected_ids = ["mpf_200"]
    check_response(request, expected_ids)

    request = '/structures?filter=nelements=1 AND NOT elements HAS "Ac"'
    expected_ids = ["mpf_200"]
    check_response(request, expected_ids)

    request = '/structures?filter=NOT elements HAS "Ac" AND nelements=1 OR nsites=1'
    expected_ids = ["mpf_1", "mpf_200"]
    check_response(request, expected_ids)

    request = '/structures?filter=elements HAS "Ac" AND nelements>1 AND nsites=1'
    expected_ids = []
    check_response(request, expected_ids)


def test_brackets(check_response):
    request = '/structures?filter=elements HAS "Ac" AND nelements=1 OR nsites=1'
    expected_ids = ["mpf_200", "mpf_1"]
    check_response(request, expected_ids)

    request = '/structures?filter=(elements HAS "Ac" AND nelements=1) OR (elements HAS "Ac" AND nsites=1)'
    expected_ids = ["mpf_1"]
    check_response(request, expected_ids)


def test_filter_on_relationships(check_response, check_error_response):

    request = '/structures?filter=references.id HAS "dummy/2019"'
    expected_ids = ["mpf_3819"]
    if CONFIG.database_backend == SupportedBackend.ELASTIC:
        check_error_response(
            request,
            expected_status=501,
            expected_title="NotImplementedError",
            expected_detail="Unable to filter on relationships with type 'references'",
        )
        pytest.xfail("Elasticsearch backend does not support relationship filtering.")
    check_response(request, expected_ids)

    request = '/structures?filter=references.id HAS ANY "dummy/2019", "dijkstra1968"'
    expected_ids = ["mpf_1", "mpf_2", "mpf_3819"]
    check_response(request, expected_ids)

    request = '/structures?filter=references.id HAS ONLY "dijkstra1968"'
    expected_ids = ["mpf_1", "mpf_2"]
    check_response(request, expected_ids)

    request = '/structures?filter=references.doi HAS ONLY "10/123"'
    error_detail = 'Cannot filter relationships by field "doi", only "id" is supported.'
    check_error_response(
        request,
        expected_status=501,
        expected_title="NotImplementedError",
        expected_detail=error_detail,
    )
