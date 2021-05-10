from optimade.filtertransformers import BaseTransformer


def test_quantity_builder(mapper):
    class DummyTransformer(BaseTransformer):
        pass

    class AwkwardMapper(mapper("StructureMapper")):

        ALIASES = (("elements", "my_elements"), ("nelements", "nelem"))
        LENGTH_ALIASES = (
            ("chemsys", "nelements"),
            ("cartesian_site_positions", "nsites"),
            ("elements", "nelements"),
        )
        PROVIDER_FIELDS = ("chemsys",)

    m = AwkwardMapper
    t = DummyTransformer(mapper=m)

    assert "_exmpl_chemsys" in t.quantities
    assert t.quantities["_exmpl_chemsys"].name == "_exmpl_chemsys"
    assert t.quantities["_exmpl_chemsys"].backend_field == "chemsys"
    assert t.quantities["_exmpl_chemsys"].length_quantity.name == "nelements"
    assert t.quantities["_exmpl_chemsys"].length_quantity.backend_field == "nelem"

    assert t.quantities["elements"].length_quantity.backend_field == "nelem"
