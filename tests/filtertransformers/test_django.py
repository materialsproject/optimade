import pytest

django = pytest.importorskip("django", reason="Django not found")

test_data = [
    ("band_gap<1", "(AND: ('calculation__band_gap__lt', '1'))"),
    (
        "(natoms >= 8) OR (nelements<5 AND stability>=0.5)",
        "(OR: ('entry__natoms__gte', '8'), (AND: ('entry__composition__ntypes__lt', '5'), ('stability__gte', '0.5')))",
    ),
    ("NOT natoms >= 8", "(NOT (AND: ('entry__natoms__gte', '8')))"),
    (
        "element = Th AND element != Na ",
        "(AND: ('composition__element_list__contains', 'Th'), (NOT (AND: ('composition__element_list__contains', 'Na'))))",
    ),
]


class TestDjangoTransformer:
    @pytest.fixture(autouse=True)
    def set_up_class(self):
        from optimade.filtertransformers.django import DjangoTransformer

        self.Transformer = DjangoTransformer()

    def test_query_conversion(self):
        for raw_q, dj_q in test_data:
            parsed_tree = self.Transformer.parse_raw_q(raw_q)
            assert str(self.Transformer.evaluate(parsed_tree)) == dj_q
