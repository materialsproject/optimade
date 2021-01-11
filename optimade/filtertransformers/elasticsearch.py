from typing import List

from lark import v_args
from elasticsearch_dsl import Q, Text, Keyword, Integer, Field
from optimade.models import CHEMICAL_SYMBOLS, ATOMIC_NUMBERS
from optimade.filtertransformers import BaseTransformer

__all__ = ("ElasticTransformer",)


_cmp_operators = {">": "gt", ">=": "gte", "<": "lt", "<=": "lte"}
_rev_cmp_operators = {">": "<", ">=": "<=", "<": ">", "<=": ">=", "=": "=", "!=": "!="}
_has_operators = {"ALL": "must", "ANY": "should"}
_length_quantities = {
    "elements": "nelements",
    "elements_rations": "nelements",
    "dimension_types": "dimension_types",
}


class Quantity:
    """Class to provide information about available quantities to the transformer.

    The elasticsearch transformer will use `Quantity`s to (a) do some semantic checks,
    (b) map quantities to the underlying elastic index.

    Attributes:
        name: The name of the quantity as used in the filter expressions.
        es_field: The name of the field for this quanity in elastic search, will be
            ``name`` by default.
        elastic_mapping_type: A decendent of an elasticsearch_dsl Field that denotes which
            mapping was used in the elastic search index.
        length_quantity: Elasticsearch does not support length of arrays, but we can
            map fields with array to other fields with ints about the array length. The
            LENGTH operator will only be supported for quantities with this attribute.
        has_only_quantity: Elasticsearch does not support exclusive search on arrays, like
            a list of chemical elements. But, we can order all elements by atomic number
            and use a keyword field with all elements to perform this search. This only
            works for elements (i.e. labels in ``CHEMICAL_SYMBOLS``) and quantities
            with this attribute.
        nested_quantity: To support optimade's 'zipped tuple' feature (e.g.
            'elements:elements_ratios HAS "H":>0.33), we use elasticsearch nested objects
            and nested queries. This quantity will provide the field for the nested
            object that contains the quantity (and others). The zipped tuples will only
            work for quantities that share the same nested object quantity.
    """

    def __init__(
        self,
        name,
        es_field: str = None,
        elastic_mapping_type: Field = None,
        length_quantity: "Quantity" = None,
        has_only_quantity: "Quantity" = None,
        nested_quantity: "Quantity" = None,
    ):

        self.name = name
        self.es_field = es_field if es_field is not None else name
        self.elastic_mapping_type = (
            Keyword if elastic_mapping_type is None else elastic_mapping_type
        )
        self.length_quantity = length_quantity
        self.has_only_quantity = has_only_quantity
        self.nested_quantity = nested_quantity

    def __repr__(self):
        return self.name


class ElasticTransformer(BaseTransformer):
    """Transformer that transforms ``v0.10.1`` grammar parse trees into queries.

    Uses elasticsearch_dsl and will produce a `Q` instance.
    """

    def __init__(self, quantities: List[Quantity]):
        """
        Arguments:
            quantities: A list of :class:`Quantity`s that describe how optimade (and other)
                quantities are mapped to the elasticsearch index.
        """
        self.index_mapping = {quantity.name: quantity for quantity in quantities}
        super().__init__()

    def _field(self, quantity, nested=None):
        if nested is not None:
            return "%s.%s" % (nested.es_field, quantity.name)

        return quantity.es_field

    def _query_op(self, quantity, op, value, nested=None):
        """
        Return a range, match, or term query for the given quantity, comparison
        operator, and value
        """
        field = self._field(quantity, nested=nested)
        if op in _cmp_operators:
            return Q("range", **{field: {_cmp_operators[op]: value}})

        if quantity.elastic_mapping_type == Text:
            query_type = "match"
        elif quantity.elastic_mapping_type in [Keyword, Integer]:
            query_type = "term"
        else:
            raise NotImplementedError("Quantity has unsupported ES field type")

        if op in ["=", ""]:
            return Q(query_type, **{field: value})

        if op == "!=":
            return ~Q(  # pylint: disable=invalid-unary-operand-type
                query_type, **{field: value}
            )

    def _has_query_op(self, quantities, op, predicate_zip_list):
        """
        Returns a bool query that combines the operator queries ():func:`_query_op`)
        for each predicate and zipped quantity pericates combinations.
        """
        if op == "HAS":
            kind = "must"  # in case of HAS we do a must over the "list" of the one given element
        elif op == "HAS ALL":
            kind = "must"
        elif op == "HAS ANY":
            kind = "should"
        elif op == "HAS ONLY":
            # HAS ONLY comes with heavy limitations, because there is no such thing
            # in elastic search. Only supported for elements, where we can construct
            # an anonymous "formula" based on elements sorted by order number and
            # can do a = comparision to check if all elements are contained
            if len(quantities) > 1:
                raise Exception("HAS ONLY is not supported with zip")
            quantity = quantities[0]

            if quantity.has_only_quantity is None:
                raise Exception("HAS ONLY is not supported by %s" % quantity.name)

            def values():
                for predicates in predicate_zip_list:
                    if len(predicates) != 1:
                        raise Exception("Tuples not supported in HAS ONLY")
                    op, value = predicates[0]
                    if op != "=":
                        raise Exception("Predicated not supported in HAS ONLY")
                    if not isinstance(value, str):
                        raise Exception("Only strings supported in HAS ONLY")
                    yield value

            try:
                order_numbers = list([ATOMIC_NUMBERS[element] for element in values()])
                order_numbers.sort()
                value = "".join(
                    [CHEMICAL_SYMBOLS[number - 1] for number in order_numbers]
                )
            except KeyError:
                raise Exception("HAS ONLY is only supported for chemical symbols")

            return Q("term", **{quantity.has_only_quantity.name: value})
        else:
            raise NotImplementedError

        queries = [
            self._has_query(quantities, predicates) for predicates in predicate_zip_list
        ]
        return Q("bool", **{kind: queries})

    def _has_query(self, quantities, predicates):
        """
        Returns a bool query that combines the operator queries ():func:`_query_op`)
        for quantity pericate combination.
        """
        if len(quantities) != len(predicates):
            raise Exception(
                "Tuple length does not match: %s <o> %s "
                % (":".join(quantities), ":".join(predicates))
            )

        if len(quantities) == 1:
            o, value = predicates[0]
            return self._query_op(quantities[0], o, value)

        nested_quantity = quantities[0].nested_quantity
        same_nested_quantity = any(
            q.nested_quantity != nested_quantity for q in quantities
        )
        if nested_quantity is None or same_nested_quantity:
            raise Exception(
                "Expression with tuples are only supported for %s"
                % ", ".join(quantities)
            )

        queries = [
            self._query_op(quantity, o, value, nested=nested_quantity)
            for quantity, (o, value) in zip(quantities, predicates)
        ]

        return Q(
            "nested",
            path=self._field(nested_quantity),
            query=dict(bool=dict(must=queries)),
        )

    def __default__(self, tree, children, *args, **kwargs):
        """ Default behavior for rules that only replace one symbol with another """
        return children[0]

    def filter(self, args):
        # filter: expression*
        if len(args) == 1:
            return args[0]
        return Q("bool", **{"must": args})

    def expression_clause(self, args):
        # expression_clause: expression_phrase ( _AND expression_phrase )*
        result = args[0]
        for arg in args[1:]:
            result &= arg
        return result

    def expression(self, args):
        # expression: expression_clause ( _OR expression_clause )*
        result = args[0]
        for arg in args[1:]:
            result |= arg
        return result

    def expression_phrase(self, args):
        # expression_phrase: [ NOT ] ( operator | "(" expression ")" )
        if args[0] == "NOT":
            return ~args[1]
        return args[0]

    @v_args(inline=True)
    def property_first_comparison(self, quantity, query):
        # property_first_comparison: property *_rhs
        return query(quantity)

    @v_args(inline=True)
    def constant_first_comparison(self, value, op, quantity):
        # constant_first_comparison: constant OPERATOR ( non_string_value | ...not_implemented_string )
        if not isinstance(quantity, Quantity):
            raise Exception("Only quantities can be compared to constant values.")

        return self._query_op(quantity, _rev_cmp_operators[op], value)

    @v_args(inline=True)
    def value_op_rhs(self, op, value):
        # value_op_rhs: OPERATOR value
        return lambda quantity: self._query_op(quantity, op, value)

    def length_op_rhs(self, args):
        # length_op_rhs: LENGTH [ OPERATOR ] signed_int
        value = args[-1]
        if len(args) == 3:
            op = args[1]
        else:
            op = "="

        def query(quantity):
            if quantity.length_quantity is None:
                raise Exception("LENGTH is not supported for %s" % quantity.name)
            quantity = quantity.length_quantity
            return self._query_op(quantity, op, value)

        return query

    @v_args(inline=True)
    def known_op_rhs(self, _, value):
        # known_op_rhs: IS ( KNOWN | UNKNOWN )

        def query(quantity):
            query = Q("exists", field=self._field(quantity))
            if value == "KNOWN":
                return query
            elif value == "UNKNOWN":
                return ~query  # pylint: disable=invalid-unary-operand-type
            raise NotImplementedError

        return query

    def set_op_rhs(self, args):
        # set_op_rhs: HAS ( [ OPERATOR ] value | ALL value_list | ... )
        values = args[-1]
        if not isinstance(values, list):
            if len(args) == 3:
                op = args[1]
            else:
                op = "="
            values = [(op, values)]

        if len(args) == 3:
            op = "HAS " + args[1]
        else:
            op = "HAS"

        return lambda quantity: self._has_query_op(
            [quantity], op, [[value] for value in values]
        )

    def set_zip_op_rhs(self, args):
        # set_zip_op_rhs: property_zip_addon HAS ( value_zip | ONLY value_zip_list | ALL value_zip_list | ANY value_zip_list )
        add_on = args[0]
        values = args[-1]
        if len(args) == 4:
            op = "HAS " + args[2]
        else:
            op = "HAS"
            values = [values]

        return lambda quantity: self._has_query_op([quantity] + add_on, op, values)

    def property_zip_addon(self, args):
        return args

    def value_zip(self, args):
        return self.value_list(args)

    def value_zip_list(self, args):
        return args

    def value_list(self, args):
        result = []
        op = "="
        for arg in args:
            if arg in ["<", "<=", ">", ">=", "!=", "="]:
                op = arg
            else:
                result.append(
                    (
                        op,
                        arg,
                    )
                )
                op = "="
        return result

    def fuzzy_string_op_rhs(self, args):
        op = args[0]
        value = args[-1]
        if op == "CONTAINS":
            wildcard = "*%s*" % value
        if op == "STARTS":
            wildcard = "%s*" % value
        if op == "ENDS":
            wildcard = "*%s" % value

        return lambda quantity: Q("wildcard", **{self._field(quantity): wildcard})

    def property(self, args):
        # property: IDENTIFIER ( "." IDENTIFIER )*
        quantity_name = args[0]

        if quantity_name not in self.index_mapping:
            raise Exception("%s is not a searchable quantity" % quantity_name)

        quantity = self.index_mapping.get(quantity_name, None)
        if quantity is None:
            quantity = Quantity(name=quantity_name)

        return quantity

    @v_args(inline=True)
    def string(self, string):
        # string: ESCAPED_STRING
        return string.strip('"')

    @v_args(inline=True)
    def signed_int(self, number):
        # signed_int : SIGNED_INT
        return int(number)

    @v_args(inline=True)
    def number(self, number):
        # number: SIGNED_INT | SIGNED_FLOAT
        if number.type == "SIGNED_INT":
            type_ = int
        elif number.type == "SIGNED_FLOAT":
            type_ = float
        return type_(number)
