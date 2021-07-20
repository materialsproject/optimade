import os
import abc
from glob import glob
from typing import Tuple

import pytest

from lark import Tree

from optimade.filterparser import LarkParser
from optimade.server.exceptions import BadRequest

testfile_dir = os.path.join(os.path.dirname(__file__), "testfiles")


class BaseTestFilterParser(abc.ABC):

    version: Tuple[int, int, int]
    variant: str = "default"

    @pytest.fixture(autouse=True)
    def set_up(self):
        self.test_filters = []
        for fn in sorted(glob(os.path.join(testfile_dir, "*.inp"))):
            with open(fn) as f:
                self.test_filters.append(f.read().strip())
        self.parser = LarkParser(version=self.version, variant=self.variant)

    def test_inputs(self):
        for tf in self.test_filters:
            if tf == "filter=number=0.0.1":
                with pytest.raises(BadRequest):
                    self.parser.parse(tf)
            else:
                tree = self.parser.parse(tf)
                assert isinstance(tree, Tree)

    def test_parser_version(self):
        assert self.parser.version == self.version
        assert self.parser.variant == self.variant

    def test_repr(self):
        assert repr(self.parser) is not None
        self.parser.parse(self.test_filters[0])
        assert repr(self.parser) is not None


class TestParserV1_0_0(BaseTestFilterParser):

    version = (1, 0, 0)
    variant = "default"

    def parse(self, inp):
        return self.parser.parse(inp)

    def test_empty(self):
        assert isinstance(self.parse(" "), Tree)

    def test_property_names(self):
        assert isinstance(self.parse("band_gap = 1"), Tree)
        assert isinstance(self.parse("cell_length_a = 1"), Tree)
        assert isinstance(self.parse("cell_volume = 1"), Tree)

        with pytest.raises(BadRequest):
            self.parse("0_kvak IS KNOWN")  # starts with a number

        with pytest.raises(BadRequest):
            self.parse('"foo bar" IS KNOWN')  # contains space; contains quotes

        with pytest.raises(BadRequest):
            self.parse("BadLuck IS KNOWN")  # contains upper-case letters

        # database-provider-specific prefixes
        assert isinstance(self.parse("_exmpl_formula_sum = 1"), Tree)
        assert isinstance(self.parse("_exmpl_band_gap = 1"), Tree)

        # Nested property names
        assert isinstance(self.parse("identifier1.identifierd2 = 42"), Tree)

    def test_string_values(self):
        assert isinstance(self.parse('author="Sąžininga Žąsis"'), Tree)
        assert isinstance(
            self.parse('field = "!#$%&\'() * +, -./:; <= > ? @[] ^ `{|}~ % "'), Tree
        )

    def test_number_values(self):
        assert isinstance(self.parse("a = 12345"), Tree)
        assert isinstance(self.parse("b = +12"), Tree)
        assert isinstance(self.parse("c = -34"), Tree)
        assert isinstance(self.parse("d = 1.2"), Tree)
        assert isinstance(self.parse("e = .2E7"), Tree)
        assert isinstance(self.parse("f = -.2E+7"), Tree)
        assert isinstance(self.parse("g = +10.01E-10"), Tree)
        assert isinstance(self.parse("h = 6.03e23"), Tree)
        assert isinstance(self.parse("i = .1E1"), Tree)
        assert isinstance(self.parse("j = -.1e1"), Tree)
        assert isinstance(self.parse("k = 1.e-12"), Tree)
        assert isinstance(self.parse("l = -.1e-12"), Tree)
        assert isinstance(self.parse("m = 1000000000.E1000000000"), Tree)

        with pytest.raises(BadRequest):
            self.parse("number=1.234D12")
        with pytest.raises(BadRequest):
            self.parse("number=.e1")
        with pytest.raises(BadRequest):
            self.parse("number= -.E1")
        with pytest.raises(BadRequest):
            self.parse("number=+.E2")
        with pytest.raises(BadRequest):
            self.parse("number=1.23E+++")
        with pytest.raises(BadRequest):
            self.parse("number=+-123")
        with pytest.raises(BadRequest):
            self.parse("number=0.0.1")

    def test_operators(self):
        # Basic boolean operations
        assert isinstance(
            self.parse(
                'NOT ( chemical_formula_hill = "Al" AND chemical_formula_anonymous = "A" OR '
                'chemical_formula_anonymous = "H2O" AND NOT chemical_formula_hill = "Ti" )'
            ),
            Tree,
        )

        # Numeric and String comparisons
        assert isinstance(self.parse("nelements > 3"), Tree)
        assert isinstance(
            self.parse(
                'chemical_formula_hill = "H2O" AND chemical_formula_anonymous != "AB"'
            ),
            Tree,
        )
        assert isinstance(
            self.parse(
                "_exmpl_aax <= +.1e8 OR nelements >= 10 AND "
                'NOT ( _exmpl_x != "Some string" OR NOT _exmpl_a = 7)'
            ),
            Tree,
        )
        assert isinstance(self.parse('_exmpl_spacegroup="P2"'), Tree)
        assert isinstance(self.parse("_exmpl_cell_volume<100.0"), Tree)
        assert isinstance(
            self.parse("_exmpl_bandgap > 5.0 AND _exmpl_molecular_weight < 350"), Tree
        )
        assert isinstance(
            self.parse('_exmpl_melting_point<300 AND nelements=4 AND elements="Si,O2"'),
            Tree,
        )
        assert isinstance(self.parse("_exmpl_some_string_property = 42"), Tree)
        assert isinstance(self.parse("5 < _exmpl_a"), Tree)

        # OPTIONAL
        assert isinstance(
            self.parse("((NOT (_exmpl_a>_exmpl_b)) AND _exmpl_x>0)"), Tree
        )
        assert isinstance(self.parse("5 < 7"), Tree)

    def test_id(self):
        assert isinstance(self.parse('id="example/1"'), Tree)
        assert isinstance(self.parse('"example/1" = id'), Tree)
        assert isinstance(self.parse('id="test/2" OR "example/1" = id'), Tree)

    def test_string_operations(self):
        #  Substring comparisons
        assert isinstance(
            self.parse(
                'chemical_formula_anonymous CONTAINS "C2" AND '
                'chemical_formula_anonymous STARTS WITH "A2"'
            ),
            Tree,
        )
        assert isinstance(
            self.parse(
                'chemical_formula_anonymous STARTS "B2" AND '
                'chemical_formula_anonymous ENDS WITH "D2"'
            ),
            Tree,
        )

    def test_list_properties(self):
        # Comparisons of list properties
        assert isinstance(self.parse("list HAS < 3"), Tree)
        assert isinstance(self.parse("list HAS ALL < 3, > 3"), Tree)
        assert isinstance(self.parse("list:list HAS >=2:<=5"), Tree)
        assert isinstance(
            self.parse(
                'elements HAS "H" AND elements HAS ALL "H","He","Ga","Ta" AND elements HAS '
                'ONLY "H","He","Ga","Ta" AND elements HAS ANY "H", "He", "Ga", "Ta"'
            ),
            Tree,
        )

        # OPTIONAL:
        assert isinstance(self.parse('elements HAS ONLY "H","He","Ga","Ta"'), Tree)
        assert isinstance(self.parse('elements HAS ALL "H","He","Ga","Ta"'), Tree)
        assert isinstance(self.parse('elements HAS ANY "H","He","Ga","Ta"'), Tree)
        assert isinstance(
            self.parse(
                'elements:_exmpl_element_counts HAS "H":6 AND '
                'elements:_exmpl_element_counts HAS ALL "H":6,"He":7 AND '
                'elements:_exmpl_element_counts HAS ONLY "H":6 AND '
                'elements:_exmpl_element_counts HAS ANY "H":6,"He":7 AND '
                'elements:_exmpl_element_counts HAS ONLY "H":6,"He":7'
            ),
            Tree,
        )
        assert isinstance(
            self.parse(
                "_exmpl_element_counts HAS < 3 AND "
                "_exmpl_element_counts HAS ANY > 3, = 6, 4, != 8"
            ),
            Tree,
        )
        assert isinstance(
            self.parse(
                "elements:_exmpl_element_counts:_exmpl_element_weights "
                'HAS ANY > 3:"He":>55.3 , = 6:>"Ti":<37.6 , 8:<"Ga":0'
            ),
            Tree,
        )

    def test_properties(self):
        #  Filtering on Properties with unknown value
        assert isinstance(
            self.parse(
                "chemical_formula_hill IS KNOWN AND "
                "NOT chemical_formula_anonymous IS UNKNOWN"
            ),
            Tree,
        )

    def test_precedence(self):
        assert isinstance(self.parse('NOT a > b OR c = 100 AND f = "C2 H6"'), Tree)
        assert isinstance(
            self.parse('(NOT (a > b)) OR ( (c = 100) AND (f = "C2 H6") )'), Tree
        )
        assert isinstance(self.parse("a >= 0 AND NOT b < c OR c = 0"), Tree)
        assert isinstance(self.parse("((a >= 0) AND (NOT (b < c))) OR (c = 0)"), Tree)

    def test_special_cases(self):
        assert isinstance(self.parse("te < st"), Tree)
        assert isinstance(self.parse('spacegroup="P2"'), Tree)
        assert isinstance(self.parse("_cod_cell_volume<100.0"), Tree)
        assert isinstance(
            self.parse("_mp_bandgap > 5.0 AND _cod_molecular_weight < 350"), Tree
        )
        assert isinstance(
            self.parse('_cod_melting_point<300 AND nelements=4 AND elements="Si,O2"'),
            Tree,
        )
        assert isinstance(self.parse("key=value"), Tree)
        assert isinstance(self.parse('author=" someone "'), Tree)
        assert isinstance(self.parse('author=" som\neone "'), Tree)
        assert isinstance(
            self.parse(
                "number=0.ANDnumber=.0ANDnumber=0.0ANDnumber=+0AND_n_u_m_b_e_r_=-0AND"
                "number=0e1ANDnumber=0e-1ANDnumber=0e+1"
            ),
            Tree,
        )

        assert isinstance(
            self.parse("NOTice=val"), Tree
        )  # property (ice) != property (val)
        assert isinstance(
            self.parse('NOTice="val"'), Tree
        )  # property (ice) != value ("val")
        assert isinstance(
            self.parse('"NOTice"=val'), Tree
        )  # value ("NOTice") = property (val)

        with pytest.raises(BadRequest):
            self.parse("NOTICE=val")  # not valid property or value (NOTICE)
        with pytest.raises(BadRequest):
            self.parse('"NOTICE"=Val')  # not valid property (Val)
        with pytest.raises(BadRequest):
            self.parse("NOTICE=val")  # not valid property or value (NOTICE)


class TestParserV1_2_0(TestParserV1_0_0):
    version = (1, 2, 0)
    variant = "develop"

    def test_boolean_values(self):
        assert isinstance(
            self.parse("_exmpl_element_counts = TRUE"),
            Tree,
        )

        assert isinstance(
            self.parse("_exmpl_element_counts = FALSE"),
            Tree,
        )

        assert isinstance(
            self.parse("_exmpl_element_counts != FALSE"),
            Tree,
        )

        assert isinstance(
            self.parse("NOT _exmpl_element_counts = TRUE"),
            Tree,
        )
