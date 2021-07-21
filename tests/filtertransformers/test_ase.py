import pytest
from optimade.filtertransformers.ase import ASETransformer
from optimade.filterparser import LarkParser


@pytest.fixture
def transform():
    transformer = ASETransformer()
    parser = LarkParser(version=(1, 0, 0))

    def f(query: str):
        return transformer.transform(parser.parse(query))

    return f


cases = [
    ("nelements=2", ("nelements", ("=", 2))),
    (
        'nelements=3 AND elements HAS "Cu"',
        ("AND", [("nelements", ("=", 3)), ("elements", ("HAS", '"Cu"'))]),
    ),
]


@pytest.mark.parametrize(["query", "tree"], cases)
def test_simple(query, tree, transform):
    assert transform(query) == tree
