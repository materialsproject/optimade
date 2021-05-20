from typing import Dict, Union, Type, Optional
from lark import v_args
from elasticsearch_dsl import Q, Text, Keyword, Integer, Field

from optimade.filtertransformers import BaseTransformer, Quantity
from optimade.server.mappers import BaseResourceMapper

__all__ = ("ElasticTransformer",)


class ElasticsearchQuantity(Quantity):
    """Elasticsearch-specific extension of the underlying
    [`Quantity`][optimade.filtertransformers.base_transformer.Quantity] class.

    Attributes:
        name: The name of the quantity as used in the filter expressions.
        backend_field: The name of the field for this quantity in Elasticsearch, will be
            ``name`` by default.
        elastic_mapping_type: A decendent of an `elasticsearch_dsl.Field` that denotes which
            mapping type was used in the Elasticsearch index.
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

    name: str
    backend_field: Optional[str]
    length_quantity: Optional["ElasticsearchQuantity"]
    elastic_mapping_type: Optional[Field]
    has_only_quantity: Optional["ElasticsearchQuantity"]
    nested_quantity: Optional["ElasticsearchQuantity"]

    def __init__(
        self,
        name: str,
        backend_field: str = None,
        length_quantity: "ElasticsearchQuantity" = None,
        elastic_mapping_type: Field = None,
        has_only_quantity: "ElasticsearchQuantity" = None,
        nested_quantity: "ElasticsearchQuantity" = None,
    ):
        """Initialise the quantity from its name, aliases and mapping type.

        Parameters:
            name: The name of the quantity as used in the filter expressions.
            backend_field: The name of the field for this quantity in Elasticsearch, will be
                ``name`` by default.
            elastic_mapping_type: A decendent of an `elasticsearch_dsl.Field` that denotes which
                mapping type was used in the Elasticsearch index.
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

        super().__init__(name, backend_field, length_quantity)

        self.elastic_mapping_type = (
            Keyword if elastic_mapping_type is None else elastic_mapping_type
        )
        self.has_only_quantity = has_only_quantity
        self.nested_quantity = nested_quantity


class ElasticTransformer(BaseTransformer):
    """Transformer that transforms ``v0.10.1``/`v1.0` grammar parse
    trees into Elasticsearch queries.

    Uses elasticsearch_dsl and will produce an `elasticsearch_dsl.Q` instance.

    """

    operator_map = {
        "<": "lt",
        "<=": "lte",
        ">": "gt",
        ">=": "gte",
    }

    _quantity_type: Type[ElasticsearchQuantity] = ElasticsearchQuantity

    def __init__(
        self, mapper: BaseResourceMapper = None, quantities: Dict[str, Quantity] = None
    ):
        if quantities is not None:
            self.quantities = quantities

        super().__init__(mapper=mapper)

    def _field(self, quantity: Union[str, Quantity], nested: Quantity = None) -> str:
        """Used to unwrap from `property` to the string backend field name.

        If passed a `Quantity` (or a derived `ElasticsearchQuantity`), this method
        returns the backend field name, modulo some handling of nested fields.

        If passed a string quantity name:
        - Check that the name does not match a relationship type,
          raising a `NotImplementedError` if it does.
        - If the string is prefixed by an underscore, assume this is a
          provider-specific field from another provider and simply return it.
          The original `property` rule would have already filtered out provider
          fields for this backend appropriately as `Quantity` objects.

        Returns:
            The field name to use for database queries.

        """

        if isinstance(quantity, str):
            if quantity in self.mapper.RELATIONSHIP_ENTRY_TYPES:
                raise NotImplementedError(
                    f"Unable to filter on relationships with type {quantity!r}"
                )

            # In this case, the property rule has already filtered out fields
            # that do not match this provider, so this indicates an "other provider"
            # field that should be passed over
            if quantity.startswith("_"):
                return quantity

        if nested is not None:
            return "%s.%s" % (nested.backend_field, quantity.name)

        return quantity.backend_field

    def _query_op(
        self,
        quantity: Union[ElasticsearchQuantity, str],
        op: str,
        value: Union[str, float, int],
        nested: ElasticsearchQuantity = None,
    ) -> Q:
        """Return a range, match, or term query for the given quantity, comparison
        operator, and value.

        Returns:
            An elasticsearch_dsl query.

        Raises:
            BadRequest: If the query is not well-defined or is not supported.
        """
        field = self._field(quantity, nested=nested)
        if op in self.operator_map:
            return Q("range", **{field: {self.operator_map[op]: value}})

        # If quantity is an "other provider" field then use Keyword as the default
        # mapping type. These queries should not match on anything as the field
        # is not present in the index.
        elastic_mapping_type = Keyword
        if isinstance(quantity, ElasticsearchQuantity):
            elastic_mapping_type = quantity.elastic_mapping_type

        if elastic_mapping_type == Text:
            query_type = "match"
        elif elastic_mapping_type in [Keyword, Integer]:
            query_type = "term"
        else:
            raise NotImplementedError("Quantity has unsupported ES field type")

        if op in ["=", ""]:
            return Q(query_type, **{field: value})

        if op == "!=":
            # != queries must also include an existence check
            # Note that for MongoDB, `$exists` will include null-valued fields,
            # where as in ES `exists` excludes them.
            # pylint: disable=invalid-unary-operand-type
            return ~Q(query_type, **{field: value}) & Q("exists", field=field)

    def _has_query_op(self, quantities, op, predicate_zip_list):
        """Returns a bool query that combines the operator calls `_query_op`
        for each predicate and zipped quantity predicate combination.
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

            # @ml-evs: Disabling this HAS ONLY workaround as tests are not passing
            raise NotImplementedError(
                "HAS ONLY queries are not currently supported by the Elasticsearch backend."
            )

            # from optimade.models import CHEMICAL_SYMBOLS, ATOMIC_NUMBERS

            # if len(quantities) > 1:
            #     raise NotImplementedError("HAS ONLY is not supported with zip")
            # quantity = quantities[0]

            # if quantity.has_only_quantity is None:
            #     raise NotImplementedError(
            #         "HAS ONLY is not supported by %s" % quantity.name
            #     )

            # def values():
            #     for predicates in predicate_zip_list:
            #         if len(predicates) != 1:
            #             raise NotImplementedError("Tuples not supported in HAS ONLY")
            #         op, value = predicates[0]
            #         if op != "=":
            #             raise NotImplementedError(
            #                 "Predicated not supported in HAS ONLY"
            #             )
            #         if not isinstance(value, str):
            #             raise NotImplementedError("Only strings supported in HAS ONLY")
            #         yield value

            # try:
            #     order_numbers = list([ATOMIC_NUMBERS[element] for element in values()])
            #     order_numbers.sort()
            #     value = "".join(
            #         [CHEMICAL_SYMBOLS[number - 1] for number in order_numbers]
            #     )
            # except KeyError:
            #     raise NotImplementedError(
            #         "HAS ONLY is only supported for chemical symbols"
            #     )

            # return Q("term", **{quantity.has_only_quantity.name: value})
        else:
            raise NotImplementedError(f"Unrecognised operation {op}.")

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
            raise ValueError(
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
            raise NotImplementedError(
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
        """Default behavior for rules that only replace one symbol with another"""
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
            raise TypeError("Only quantities can be compared to constant values.")

        return self._query_op(quantity, self._reversed_operator_map[op], value)

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

            # This is only the case if quantity is an "other" provider's field,
            # in which case, we should treat it as unknown and try to do a null query
            if isinstance(quantity, str):
                return self._query_op(quantity, op, value)

            if quantity.length_quantity is None:
                raise NotImplementedError(
                    f"LENGTH is not supported for {quantity.name!r}"
                )
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
        raise NotImplementedError("Correlated list queries are not supported.")
        return args

    def value_zip(self, args):
        raise NotImplementedError("Correlated list queries are not supported.")
        return self.value_list(args)

    def value_zip_list(self, args):
        raise NotImplementedError("Correlated list queries are not supported.")
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
