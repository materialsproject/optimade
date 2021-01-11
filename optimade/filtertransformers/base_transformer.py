import abc
from lark import Transformer, v_args
from typing import Dict
from optimade.server.mappers import BaseResourceMapper

__all__ = ("BaseTransformer",)


class BaseTransformer(abc.ABC, Transformer):
    """Generic filter transformer that handles various
    parts of the grammar in a backend non-specific way.

    """

    # map from standard comparison operators to the backend-specific version
    operator_map: Dict[str, str] = {
        "<": None,
        "<=": None,
        ">": None,
        ">=": None,
        "!=": None,
        "=": None,
    }

    # map from back-end specific operators to their inverse
    # e.g. {"$lt": "$gt"} for MongoDB.
    reversed_operator_map: Dict[str, str] = {}

    def __init__(self, mapper: BaseResourceMapper = None):
        """Initialise the transformer object, optionally loading in a
        resource mapper for use when post-processing.

        """
        self.mapper = mapper

    def postprocess(self, query):
        """Post-process the query according to the rules defined for
        the backend.

        """
        return query

    def transform(self, tree):
        """ Transform the query using the Lark transformer then post-process. """
        return self.postprocess(super().transform(tree))

    def __default__(self, data, children, meta):
        raise NotImplementedError(
            f"Calling __default__, i.e., unknown grammar concept. data: {data}, children: {children}, meta: {meta}"
        )

    def filter(self, arg):
        """ filter: expression* """
        return arg[0] if arg else None

    @v_args(inline=True)
    def constant(self, value):
        """ constant: string | number """
        # Note: Return as is.
        return value

    @v_args(inline=True)
    def value(self, value):
        """ value: string | number | property """
        # Note: Return as is.
        return value

    @v_args(inline=True)
    def non_string_value(self, value):
        """ non_string_value: number | property """
        # Note: Return as is.
        return value

    @v_args(inline=True)
    def not_implemented_string(self, value):
        """not_implemented_string: value

        Raises:
            NotImplementedError: For further information, see Materials-Consortia/OPTIMADE issue 157:
                https://github.com/Materials-Consortia/OPTIMADE/issues/157

        """
        raise NotImplementedError("Comparing strings is not yet implemented.")

    def property(self, arg):
        """ property: IDENTIFIER ( "." IDENTIFIER )* """
        return ".".join(arg)

    @v_args(inline=True)
    def string(self, string):
        """ string: ESCAPED_STRING """
        return string.strip('"')

    @v_args(inline=True)
    def signed_int(self, number):
        """ signed_int : SIGNED_INT """
        return int(number)

    @v_args(inline=True)
    def number(self, number):
        """ number: SIGNED_INT | SIGNED_FLOAT """
        if number.type == "SIGNED_INT":
            type_ = int
        elif number.type == "SIGNED_FLOAT":
            type_ = float
        return type_(number)

    @v_args(inline=True)
    def comparison(self, value):
        """ comparison: constant_first_comparison | property_first_comparison """
        # Note: Return as is.
        return value

    @abc.abstractmethod
    def value_list(self, arg):
        """ value_list: [ OPERATOR ] value ( "," [ OPERATOR ] value )* """

    @abc.abstractmethod
    def value_zip(self, arg):
        """ value_zip: [ OPERATOR ] value ":" [ OPERATOR ] value (":" [ OPERATOR ] value)* """

    @abc.abstractmethod
    def value_zip_list(self, arg):
        """ value_zip_list: value_zip ( "," value_zip )* """

    @abc.abstractmethod
    def expression(self, arg):
        """ expression: expression_clause ( OR expression_clause ) """

    @abc.abstractmethod
    def expression_clause(self, arg):
        """ expression_clause: expression_phrase ( AND expression_phrase )* """

    @abc.abstractmethod
    def expression_phrase(self, arg):
        """ expression_phrase: [ NOT ] ( comparison | "(" expression ")" ) """

    @abc.abstractmethod
    def property_first_comparison(self, arg):
        """property_first_comparison: property ( value_op_rhs | known_op_rhs | fuzzy_string_op_rhs | set_op_rhs |
        set_zip_op_rhs | length_op_rhs )

        """

    @abc.abstractmethod
    def constant_first_comparison(self, arg):
        """ constant_first_comparison: constant OPERATOR ( non_string_value | not_implemented_string ) """

    @v_args(inline=True)
    @abc.abstractmethod
    def value_op_rhs(self, operator, value):
        """ value_op_rhs: OPERATOR value """

    @abc.abstractmethod
    def known_op_rhs(self, arg):
        """ known_op_rhs: IS ( KNOWN | UNKNOWN ) """

    @abc.abstractmethod
    def fuzzy_string_op_rhs(self, arg):
        """ fuzzy_string_op_rhs: CONTAINS value | STARTS [ WITH ] value | ENDS [ WITH ] value """

    @abc.abstractmethod
    def set_op_rhs(self, arg):
        """ set_op_rhs: HAS ( [ OPERATOR ] value | ALL value_list | ANY value_list | ONLY value_list ) """

    @abc.abstractmethod
    def length_op_rhs(self, arg):
        """ length_op_rhs: LENGTH [ OPERATOR ] value """

    @abc.abstractmethod
    def set_zip_op_rhs(self, arg):
        """set_zip_op_rhs: property_zip_addon HAS ( value_zip | ONLY value_zip_list | ALL value_zip_list |
        ANY value_zip_list )

        """

    @abc.abstractmethod
    def property_zip_addon(self, arg):
        """ property_zip_addon: ":" property (":" property)* """
