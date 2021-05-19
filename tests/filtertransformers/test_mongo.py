import pytest

from lark.exceptions import VisitError

from optimade.filterparser import LarkParser, ParserError


class TestMongoTransformer:
    version = (1, 0, 0)
    variant = "default"

    @pytest.fixture(autouse=True)
    def set_up(self):
        from optimade.filtertransformers.mongo import MongoTransformer

        p = LarkParser(version=self.version, variant=self.variant)
        t = MongoTransformer()
        self.transform = lambda inp: t.transform(p.parse(inp))

    def test_empty(self):
        assert self.transform(" ") is None

    def test_property_names(self):
        assert self.transform("band_gap = 1") == {"band_gap": {"$eq": 1}}
        assert self.transform("cell_length_a = 1") == {"cell_length_a": {"$eq": 1}}
        assert self.transform("cell_volume = 1") == {"cell_volume": {"$eq": 1}}

        with pytest.raises(ParserError):
            self.transform("0_kvak IS KNOWN")  # starts with a number

        with pytest.raises(ParserError):
            self.transform('"foo bar" IS KNOWN')  # contains space; contains quotes

        with pytest.raises(ParserError):
            self.transform("BadLuck IS KNOWN")  # contains upper-case letters

    def test_provider_property_name(self):
        # database-provider-specific prefixes
        assert self.transform("_exmpl_formula_sum = 1") == {
            "_exmpl_formula_sum": {"$eq": 1}
        }
        assert self.transform("_exmpl_band_gap = 1") == {"_exmpl_band_gap": {"$eq": 1}}

    def test_nested_property_names(self):
        # Nested property names
        assert self.transform("identifier1.identifierd2 = 42") == {
            "identifier1.identifierd2": {"$eq": 42}
        }

    def test_string_values(self):
        assert self.transform('author="Sąžininga Žąsis"') == {
            "author": {"$eq": "Sąžininga Žąsis"}
        }
        assert self.transform(
            'field = "!#$%&\'() * +, -./:; <= > ? @[] ^ `{|}~ % "'
        ) == {"field": {"$eq": "!#$%&'() * +, -./:; <= > ? @[] ^ `{|}~ % "}}

    def test_number_values(self):
        assert self.transform("a = 12345") == {"a": {"$eq": 12345}}
        assert self.transform("b = +12") == {"b": {"$eq": 12}}
        assert self.transform("c = -34") == {"c": {"$eq": -34}}
        assert self.transform("d = 1.2") == {"d": {"$eq": 1.2}}
        assert self.transform("e = .2E7") == {"e": {"$eq": 2000000.0}}
        assert self.transform("f = -.2E+7") == {"f": {"$eq": -2000000.0}}
        assert self.transform("g = +10.01E-10") == {"g": {"$eq": 1.001e-09}}
        assert self.transform("h = 6.03e23") == {"h": {"$eq": 6.03e23}}
        assert self.transform("i = .1E1") == {"i": {"$eq": 1.0}}
        assert self.transform("j = -.1e1") == {"j": {"$eq": -1.0}}
        assert self.transform("k = 1.e-12") == {"k": {"$eq": 1e-12}}
        assert self.transform("l = -.1e-12") == {"l": {"$eq": -1e-13}}
        assert self.transform("m = 1000000000.E1000000000") == {
            "m": {"$eq": float("inf")}
        }

        with pytest.raises(ParserError):
            self.transform("number=1.234D12")
        with pytest.raises(ParserError):
            self.transform("number=.e1")
        with pytest.raises(ParserError):
            self.transform("number= -.E1")
        with pytest.raises(ParserError):
            self.transform("number=+.E2")
        with pytest.raises(ParserError):
            self.transform("number=1.23E+++")
        with pytest.raises(ParserError):
            self.transform("number=+-123")
        with pytest.raises(ParserError):
            self.transform("number=0.0.1")

    def test_simple_comparisons(self):
        assert self.transform("a<3") == {"a": {"$lt": 3}}
        assert self.transform("a<=3") == {"a": {"$lte": 3}}
        assert self.transform("a>3") == {"a": {"$gt": 3}}
        assert self.transform("a>=3") == {"a": {"$gte": 3}}
        assert self.transform("a=3") == {"a": {"$eq": 3}}
        assert self.transform("a!=3") == {
            "$and": [{"a": {"$ne": 3}}, {"a": {"$ne": None}}]
        }

    def test_id(self):
        assert self.transform('id="example/1"') == {"id": {"$eq": "example/1"}}
        assert self.transform('"example/1" = id') == {"id": {"$eq": "example/1"}}
        assert self.transform('id="test/2" OR "example/1" = id') == {
            "$or": [{"id": {"$eq": "test/2"}}, {"id": {"$eq": "example/1"}}]
        }

    def test_operators(self):
        # Basic boolean operations
        # TODO: {"a": {"$not": {"$lt": 3}}} can be simplified to {"a": {"$gte": 3}}
        assert self.transform("NOT a<3") == {"a": {"$not": {"$lt": 3}}}

        # TODO: {'$not': {'$eq': 'Ti'}} can be simplified to {'$ne': 'Ti'}
        assert self.transform(
            "NOT ( "
            'chemical_formula_hill = "Al" AND chemical_formula_anonymous = "A" OR '
            'chemical_formula_anonymous = "H2O" AND NOT chemical_formula_hill = "Ti" '
            ")"
        ) == {
            "$nor": [
                {
                    "$and": [
                        {"chemical_formula_hill": {"$eq": "Al"}},
                        {"chemical_formula_anonymous": {"$eq": "A"}},
                    ]
                },
                {
                    "$and": [
                        {"chemical_formula_anonymous": {"$eq": "H2O"}},
                        {"chemical_formula_hill": {"$not": {"$eq": "Ti"}}},
                    ]
                },
            ]
        }

        # Numeric and String comparisons
        assert self.transform("nelements > 3") == {"nelements": {"$gt": 3}}
        assert self.transform(
            'chemical_formula_hill = "H2O" AND chemical_formula_anonymous != "AB"'
        ) == {
            "$and": [
                {"chemical_formula_hill": {"$eq": "H2O"}},
                {
                    "$and": [
                        {"chemical_formula_anonymous": {"$ne": "AB"}},
                        {"chemical_formula_anonymous": {"$ne": None}},
                    ]
                },
            ]
        }
        assert self.transform(
            "_exmpl_aax <= +.1e8 OR nelements >= 10 AND "
            'NOT ( _exmpl_x != "Some string" OR NOT _exmpl_a = 7)'
        ) == {
            "$or": [
                {"_exmpl_aax": {"$lte": 10000000.0}},
                {
                    "$and": [
                        {"nelements": {"$gte": 10}},
                        {
                            "$nor": [
                                {
                                    "$and": [
                                        {"_exmpl_x": {"$ne": "Some string"}},
                                        {"_exmpl_x": {"$ne": None}},
                                    ]
                                },
                                {"_exmpl_a": {"$not": {"$eq": 7}}},
                            ]
                        },
                    ]
                },
            ]
        }
        assert self.transform('_exmpl_spacegroup="P2"') == {
            "_exmpl_spacegroup": {"$eq": "P2"}
        }
        assert self.transform("_exmpl_cell_volume<100.0") == {
            "_exmpl_cell_volume": {"$lt": 100.0}
        }
        assert self.transform(
            "_exmpl_bandgap > 5.0 AND _exmpl_molecular_weight < 350"
        ) == {
            "$and": [
                {"_exmpl_bandgap": {"$gt": 5.0}},
                {"_exmpl_molecular_weight": {"$lt": 350}},
            ]
        }
        assert self.transform(
            '_exmpl_melting_point<300 AND nelements=4 AND elements="Si,O2"'
        ) == {
            "$and": [
                {"_exmpl_melting_point": {"$lt": 300}},
                {"nelements": {"$eq": 4}},
                {"elements": {"$eq": "Si,O2"}},
            ]
        }
        assert self.transform("_exmpl_some_string_property = 42") == {
            "_exmpl_some_string_property": {"$eq": 42}
        }
        assert self.transform("5 < _exmpl_a") == {"_exmpl_a": {"$gt": 5}}

        assert self.transform("a<5 AND b=0") == {
            "$and": [{"a": {"$lt": 5}}, {"b": {"$eq": 0}}]
        }
        assert self.transform("a >= 8 OR a<5 AND b>=8") == {
            "$or": [
                {"a": {"$gte": 8}},
                {"$and": [{"a": {"$lt": 5}}, {"b": {"$gte": 8}}]},
            ]
        }

        # OPTIONAL
        # assert self.transform("((NOT (_exmpl_a>_exmpl_b)) AND _exmpl_x>0)") == {}

        assert self.transform("NOT (a>1 AND b>1)") == {
            "$and": [{"a": {"$not": {"$gt": 1}}}, {"b": {"$not": {"$gt": 1}}}]
        }

        assert self.transform("NOT (a>1 AND b>1 OR c>1)") == {
            "$nor": [
                {"$and": [{"a": {"$gt": 1}}, {"b": {"$gt": 1}}]},
                {"c": {"$gt": 1}},
            ]
        }

        assert self.transform("NOT (a>1 AND ( b>1 OR c>1 ))") == {
            "$and": [
                {"a": {"$not": {"$gt": 1}}},
                {"$nor": [{"b": {"$gt": 1}}, {"c": {"$gt": 1}}]},
            ]
        }

        assert self.transform("NOT (a>1 AND ( b>1 OR (c>1 AND d>1 ) ))") == {
            "$and": [
                {"a": {"$not": {"$gt": 1}}},
                {
                    "$nor": [
                        {"b": {"$gt": 1}},
                        {"$and": [{"c": {"$gt": 1}}, {"d": {"$gt": 1}}]},
                    ]
                },
            ]
        }

        assert self.transform(
            'elements HAS "Ag" AND NOT ( elements HAS "Ir" AND elements HAS "Ac" )'
        ) == {
            "$and": [
                {"elements": {"$in": ["Ag"]}},
                {
                    "$and": [
                        {"elements": {"$not": {"$in": ["Ir"]}}},
                        {"elements": {"$not": {"$in": ["Ac"]}}},
                    ]
                },
            ]
        }

        assert self.transform("5 < 7") == {7: {"$gt": 5}}

        with pytest.raises(VisitError):
            self.transform('"some string" > "some other string"')

    def test_filtering_on_relationships(self, mapper):
        """Test the nested properties with special names
        like "structures", "references" etc. are applied
        to the relationships field.

        """
        from optimade.filtertransformers.mongo import MongoTransformer

        t = MongoTransformer(mapper=mapper("StructureMapper"))
        p = LarkParser(version=self.version, variant=self.variant)

        assert t.transform(p.parse('references.id HAS "dummy/2019"')) == {
            "relationships.references.data.id": {"$in": ["dummy/2019"]}
        }

        assert t.transform(
            p.parse('structures.id HAS ANY "dummy/2019", "dijkstra1968"')
        ) == {
            "relationships.structures.data.id": {"$in": ["dummy/2019", "dijkstra1968"]}
        }

        assert t.transform(
            p.parse('structures.id HAS ALL "dummy/2019", "dijkstra1968"')
        ) == {
            "relationships.structures.data.id": {"$all": ["dummy/2019", "dijkstra1968"]}
        }

        assert t.transform(p.parse('structures.id HAS ONLY "dummy/2019"')) == {
            "$and": [
                {"relationships.structures.data": {"$size": 1, "$exists": True}},
                {"relationships.structures.data.id": {"$all": ["dummy/2019"]}},
            ]
        }

        assert t.transform(
            p.parse(
                'structures.id HAS ONLY "dummy/2019" AND structures.id HAS "dummy/2019"'
            )
        ) == {
            "$and": [
                {
                    "$and": [
                        {
                            "relationships.structures.data": {
                                "$size": 1,
                                "$exists": True,
                            }
                        },
                        {"relationships.structures.data.id": {"$all": ["dummy/2019"]}},
                    ]
                },
                {"relationships.structures.data.id": {"$in": ["dummy/2019"]}},
            ],
        }

    def test_other_provider_fields(self, mapper):
        """Test that fields from other providers generate
        queries that treat the value of the field as `null`.

        """
        from optimade.filtertransformers.mongo import MongoTransformer

        t = MongoTransformer(mapper=mapper("StructureMapper"))
        p = LarkParser(version=self.version, variant=self.variant)
        assert t.transform(p.parse("_other_provider_field > 1")) == {
            "_other_provider_field": {"$gt": 1}
        }

    def test_not_implemented(self):
        """Test that list properties that are currently not implemented
        give a sensible response.

        """
        # NOTE: Lark catches underlying filtertransformer exceptions and
        # raises VisitErrors, most of these actually correspond to NotImplementedError
        with pytest.raises(VisitError, match="not implemented"):
            self.transform("list HAS < 3")

        with pytest.raises(VisitError, match="not implemented"):
            self.transform("list HAS ALL < 3, > 3")

        with pytest.raises(VisitError, match="not implemented"):
            self.transform("list HAS ANY > 3, < 6")

        assert self.transform("list LENGTH 3") == {
            "list": {"$size": 3, "$exists": True}
        }

        with pytest.raises(VisitError):
            self.transform("list:list HAS >=2:<=5")

        with pytest.raises(VisitError):
            self.transform(
                'elements:_exmpl_element_counts HAS "H":6 AND elements:_exmpl_element_counts '
                'HAS ALL "H":6,"He":7 AND elements:_exmpl_element_counts HAS ONLY "H":6 AND '
                'elements:_exmpl_element_counts HAS ANY "H":6,"He":7 AND '
                'elements:_exmpl_element_counts HAS ONLY "H":6,"He":7'
            )

        with pytest.raises(VisitError):
            self.transform(
                "_exmpl_element_counts HAS < 3 AND _exmpl_element_counts "
                "HAS ANY > 3, = 6, 4, != 8"
            )

        with pytest.raises(VisitError):
            self.transform(
                "elements:_exmpl_element_counts:_exmpl_element_weights "
                'HAS ANY > 3:"He":>55.3 , = 6:>"Ti":<37.6 , 8:<"Ga":0'
            )

        assert self.transform("list LENGTH > 3") == {"list.4": {"$exists": True}}

    def test_list_length_aliases(self, mapper):
        from optimade.filtertransformers.mongo import MongoTransformer

        transformer = MongoTransformer(mapper=mapper("StructureMapper"))
        parser = LarkParser(version=self.version, variant=self.variant)

        assert transformer.transform(parser.parse("elements LENGTH 3")) == {
            "nelements": 3
        }

        assert transformer.transform(
            parser.parse('elements HAS "Li" AND elements LENGTH = 3')
        ) == {"$and": [{"elements": {"$in": ["Li"]}}, {"nelements": 3}]}

        assert transformer.transform(parser.parse("elements LENGTH > 3")) == {
            "nelements": {"$gt": 3}
        }
        assert transformer.transform(parser.parse("elements LENGTH < 3")) == {
            "nelements": {"$lt": 3}
        }
        assert transformer.transform(parser.parse("elements LENGTH = 3")) == {
            "nelements": 3
        }
        assert transformer.transform(
            parser.parse("cartesian_site_positions LENGTH <= 3")
        ) == {"nsites": {"$lte": 3}}
        assert transformer.transform(
            parser.parse("cartesian_site_positions LENGTH >= 3")
        ) == {"nsites": {"$gte": 3}}

    def test_suspected_timestamp_fields(self, mapper):
        import datetime
        import bson.tz_util
        from optimade.filtertransformers.mongo import MongoTransformer
        from optimade.server.warnings import TimestampNotRFCCompliant

        example_RFC3339_date = "2019-06-08T04:13:37Z"
        example_RFC3339_date_2 = "2019-06-08T04:13:37"
        example_non_RFC3339_date = "2019-06-08T04:13:37.123Z"

        expected_datetime = datetime.datetime(
            year=2019,
            month=6,
            day=8,
            hour=4,
            minute=13,
            second=37,
            microsecond=0,
            tzinfo=bson.tz_util.utc,
        )

        assert self.transform(f'last_modified > "{example_RFC3339_date}"') == {
            "last_modified": {"$gt": expected_datetime}
        }
        assert self.transform(f'last_modified > "{example_RFC3339_date_2}"') == {
            "last_modified": {"$gt": expected_datetime}
        }

        non_rfc_datetime = expected_datetime.replace(microsecond=123000)

        with pytest.warns(TimestampNotRFCCompliant):
            assert self.transform(f'last_modified > "{example_non_RFC3339_date}"') == {
                "last_modified": {"$gt": non_rfc_datetime}
            }

        class MyMapper(mapper("StructureMapper")):
            ALIASES = (("last_modified", "ctime"),)

        transformer = MongoTransformer(mapper=MyMapper)
        parser = LarkParser(version=self.version, variant=self.variant)

        assert transformer.transform(
            parser.parse(f'last_modified > "{example_RFC3339_date}"')
        ) == {"ctime": {"$gt": expected_datetime}}
        assert transformer.transform(
            parser.parse(f'last_modified > "{example_RFC3339_date_2}"')
        ) == {"ctime": {"$gt": expected_datetime}}

    def test_unaliased_length_operator(self):
        assert self.transform("cartesian_site_positions LENGTH <= 3") == {
            "cartesian_site_positions.4": {"$exists": False}
        }
        assert self.transform("cartesian_site_positions LENGTH < 3") == {
            "cartesian_site_positions.3": {"$exists": False}
        }
        assert self.transform("cartesian_site_positions LENGTH 3") == {
            "cartesian_site_positions": {"$size": 3, "$exists": True}
        }
        assert self.transform("cartesian_site_positions LENGTH >= 10") == {
            "cartesian_site_positions.10": {"$exists": True}
        }

        assert self.transform("cartesian_site_positions LENGTH > 10") == {
            "cartesian_site_positions.11": {"$exists": True}
        }

    def test_mongo_special_id(self, mapper):

        from optimade.filtertransformers.mongo import MongoTransformer
        from bson import ObjectId

        class MyMapper(mapper("StructureMapper")):
            ALIASES = (("immutable_id", "_id"),)

        transformer = MongoTransformer(mapper=MyMapper)
        parser = LarkParser(version=self.version, variant=self.variant)

        assert transformer.transform(
            parser.parse('immutable_id = "5cfb441f053b174410700d02"')
        ) == {"_id": {"$eq": ObjectId("5cfb441f053b174410700d02")}}

        assert transformer.transform(
            parser.parse('immutable_id != "5cfb441f053b174410700d02"')
        ) == {
            "$and": [
                {"_id": {"$ne": ObjectId("5cfb441f053b174410700d02")}},
                {"_id": {"$ne": None}},
            ]
        }

        for op in ("CONTAINS", "STARTS WITH", "ENDS WITH", "HAS"):
            with pytest.raises(
                NotImplementedError,
                match=r".*not supported for query on field 'immutable_id', can only test for equality.*",
            ):
                transformer.transform(parser.parse(f'immutable_id {op} "abcdef"'))

    def test_aliased_length_operator(self, mapper):
        from optimade.filtertransformers.mongo import MongoTransformer

        class MyMapper(mapper("StructureMapper")):
            ALIASES = (
                ("elements", "my_elements"),
                ("nelements", "nelem"),
                ("elements_ratios", "ratios"),
            )
            LENGTH_ALIASES = (
                ("chemsys", "nelements"),
                ("cartesian_site_positions", "nsites"),
                ("elements", "nelements"),
            )
            PROVIDER_FIELDS = ("chemsys",)

        m = MyMapper
        transformer = MongoTransformer(mapper=m)
        parser = LarkParser(version=self.version, variant=self.variant)

        assert transformer.transform(
            parser.parse("cartesian_site_positions LENGTH <= 3")
        ) == {"nsites": {"$lte": 3}}
        assert transformer.transform(
            parser.parse("cartesian_site_positions LENGTH < 3")
        ) == {"nsites": {"$lt": 3}}
        assert transformer.transform(
            parser.parse("cartesian_site_positions LENGTH = 3")
        ) == {"nsites": 3}
        assert transformer.transform(
            parser.parse("cartesian_site_positions LENGTH 3")
        ) == {"nsites": 3}

        assert transformer.transform(parser.parse("elements_ratios LENGTH 3")) == {
            "ratios": {"$size": 3, "$exists": True}
        }

        assert transformer.transform(
            parser.parse("cartesian_site_positions LENGTH >= 10")
        ) == {"nsites": {"$gte": 10}}

        assert transformer.transform(
            parser.parse("structure_features LENGTH > 10")
        ) == {"structure_features.11": {"$exists": True}}

        assert transformer.transform(parser.parse("nsites LENGTH > 10")) == {
            "nsites.11": {"$exists": True}
        }

        assert transformer.transform(parser.parse("elements LENGTH 3")) == {"nelem": 3}

        assert transformer.transform(parser.parse('elements HAS "Ag"')) == {
            "my_elements": {"$in": ["Ag"]}
        }

        assert transformer.transform(parser.parse("_exmpl_chemsys LENGTH 3")) == {
            "nelem": 3
        }

    def test_aliases(self, mapper):
        """Test that valid aliases are allowed, but do not affect r-values."""
        from optimade.filtertransformers.mongo import MongoTransformer

        class MyStructureMapper(mapper("StructureMapper")):
            ALIASES = (
                ("elements", "my_elements"),
                ("A", "D"),
                ("property_a", "D"),
                ("B", "E"),
                ("C", "F"),
                ("_exmpl_nested_field", "nested_field"),
            )

            PROVIDER_FIELDS = ("D", "E", "F", "nested_field")

        mapper = MyStructureMapper
        t = MongoTransformer(mapper=mapper)
        p = LarkParser(version=self.version, variant=self.variant)

        assert mapper.get_backend_field("elements") == "my_elements"
        test_filter = 'elements HAS "A"'
        assert t.transform(p.parse(test_filter)) == {"my_elements": {"$in": ["A"]}}
        test_filter = 'elements HAS ANY "A","B","C" AND elements HAS "D"'
        assert t.transform(p.parse(test_filter)) == {
            "$and": [
                {"my_elements": {"$in": ["A", "B", "C"]}},
                {"my_elements": {"$in": ["D"]}},
            ]
        }
        test_filter = 'elements = "A"'
        assert t.transform(p.parse(test_filter)) == {"my_elements": {"$eq": "A"}}
        test_filter = 'property_a HAS "B"'
        assert t.transform(p.parse(test_filter)) == {"D": {"$in": ["B"]}}

        test_filter = "_exmpl_nested_field.sub_property > 1234.5"
        assert t.transform(p.parse(test_filter)) == {
            "nested_field.sub_property": {"$gt": 1234.5}
        }

        test_filter = "_exmpl_nested_field.sub_property.x IS UNKNOWN"
        assert t.transform(p.parse(test_filter)) == {
            "$or": [
                {"nested_field.sub_property.x": {"$exists": False}},
                {"nested_field.sub_property.x": {"$eq": None}},
            ]
        }

    def test_list_properties(self):
        """Test the HAS ALL, ANY and optional ONLY queries."""
        assert self.transform('elements HAS ONLY "H","He","Ga","Ta"') == {
            "elements": {"$all": ["H", "He", "Ga", "Ta"], "$size": 4, "$exists": True}
        }

        assert self.transform('elements HAS ANY "H","He","Ga","Ta"') == {
            "elements": {"$in": ["H", "He", "Ga", "Ta"]}
        }

        assert self.transform('elements HAS ALL "H","He","Ga","Ta"') == {
            "elements": {"$all": ["H", "He", "Ga", "Ta"]}
        }

        assert self.transform(
            'elements HAS "H" AND elements HAS ALL "H","He","Ga","Ta" AND elements HAS '
            'ONLY "H","He","Ga","Ta" AND elements HAS ANY "H", "He", "Ga", "Ta"'
        ) == {
            "$and": [
                {"elements": {"$in": ["H"]}},
                {"elements": {"$all": ["H", "He", "Ga", "Ta"]}},
                {
                    "elements": {
                        "$all": ["H", "He", "Ga", "Ta"],
                        "$size": 4,
                        "$exists": True,
                    }
                },
                {"elements": {"$in": ["H", "He", "Ga", "Ta"]}},
            ]
        }

    def test_known_properties(self):
        #  Filtering on Properties with unknown value
        assert self.transform("chemical_formula_anonymous IS UNKNOWN") == {
            "$or": [
                {"chemical_formula_anonymous": {"$exists": False}},
                {"chemical_formula_anonymous": {"$eq": None}},
            ]
        }
        assert self.transform("chemical_formula_anonymous IS KNOWN") == {
            "$and": [
                {"chemical_formula_anonymous": {"$exists": True}},
                {"chemical_formula_anonymous": {"$ne": None}},
            ]
        }
        assert self.transform("NOT chemical_formula_anonymous IS UNKNOWN") == {
            "$and": [
                {"chemical_formula_anonymous": {"$exists": True}},
                {"chemical_formula_anonymous": {"$ne": None}},
            ]
        }
        assert self.transform("NOT chemical_formula_anonymous IS KNOWN") == {
            "$or": [
                {"chemical_formula_anonymous": {"$exists": False}},
                {"chemical_formula_anonymous": {"$eq": None}},
            ]
        }

        assert self.transform(
            "chemical_formula_hill IS KNOWN AND NOT chemical_formula_anonymous IS UNKNOWN"
        ) == {
            "$and": [
                {
                    "$and": [
                        {"chemical_formula_hill": {"$exists": True}},
                        {"chemical_formula_hill": {"$ne": None}},
                    ]
                },
                {
                    "$and": [
                        {"chemical_formula_anonymous": {"$exists": True}},
                        {"chemical_formula_anonymous": {"$ne": None}},
                    ]
                },
            ]
        }

        assert self.transform(
            "chemical_formula_hill IS KNOWN AND chemical_formula_anonymous IS UNKNOWN"
        ) == {
            "$and": [
                {
                    "$and": [
                        {"chemical_formula_hill": {"$exists": True}},
                        {"chemical_formula_hill": {"$ne": None}},
                    ]
                },
                {
                    "$or": [
                        {"chemical_formula_anonymous": {"$exists": False}},
                        {"chemical_formula_anonymous": {"$eq": None}},
                    ]
                },
            ]
        }

    def test_precedence(self):
        assert self.transform('NOT a > b OR c = 100 AND f = "C2 H6"') == {
            "$or": [
                {"a": {"$not": {"$gt": "b"}}},
                {"$and": [{"c": {"$eq": 100}}, {"f": {"$eq": "C2 H6"}}]},
            ]
        }
        assert self.transform('NOT a > b OR c = 100 AND f = "C2 H6"') == self.transform(
            '(NOT (a > b)) OR ( (c = 100) AND (f = "C2 H6") )'
        )
        assert self.transform("a >= 0 AND NOT b < c OR c = 0") == self.transform(
            "((a >= 0) AND (NOT (b < c))) OR (c = 0)"
        )

    def test_special_cases(self):
        assert self.transform("te < st") == {"te": {"$lt": "st"}}
        assert self.transform('spacegroup="P2"') == {"spacegroup": {"$eq": "P2"}}
        assert self.transform("_cod_cell_volume<100.0") == {
            "_cod_cell_volume": {"$lt": 100.0}
        }
        assert self.transform("_mp_bandgap > 5.0 AND _cod_molecular_weight < 350") == {
            "$and": [
                {"_mp_bandgap": {"$gt": 5.0}},
                {"_cod_molecular_weight": {"$lt": 350}},
            ]
        }
        assert self.transform(
            '_cod_melting_point<300 AND nelements=4 AND elements="Si,O2"'
        ) == {
            "$and": [
                {"_cod_melting_point": {"$lt": 300}},
                {"nelements": {"$eq": 4}},
                {"elements": {"$eq": "Si,O2"}},
            ]
        }
        assert self.transform("key=value") == {"key": {"$eq": "value"}}
        assert self.transform('author=" someone "') == {"author": {"$eq": " someone "}}
        assert self.transform("notice=val") == {"notice": {"$eq": "val"}}
        assert self.transform("NOTice=val") == {"ice": {"$not": {"$eq": "val"}}}
        assert self.transform(
            "number=0.ANDnumber=.0ANDnumber=0.0ANDnumber=+0AND_n_u_m_b_e_r_=-0AND"
            "number=0e1ANDnumber=0e-1ANDnumber=0e+1"
        ) == {
            "$and": [
                {"number": {"$eq": 0.0}},
                {"number": {"$eq": 0.0}},
                {"number": {"$eq": 0.0}},
                {"number": {"$eq": 0}},
                {"_n_u_m_b_e_r_": {"$eq": 0}},
                {"number": {"$eq": 0.0}},
                {"number": {"$eq": 0.0}},
                {"number": {"$eq": 0.0}},
            ]
        }
