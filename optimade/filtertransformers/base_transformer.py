"""This submodule implements the
[`BaseTransformer`][optimade.filtertransformers.base_transformer.BaseTransformer]
and [`Quantity`][optimade.filtertransformers.base_transformer.Quantity] classes
for turning filters parsed by lark into backend-specific queries.

"""

import abc
from typing import Dict, Any, Type, Optional
import warnings

from lark import Transformer, v_args, Tree

from optimade.server.mappers import BaseResourceMapper
from optimade.server.exceptions import BadRequest
from optimade.server.warnings import UnknownProviderProperty


__all__ = (
    "BaseTransformer",
    "Quantity",
)


class Quantity:
    """Class to provide information about available quantities to the transformer.

    The transformer can use [`Quantity`][optimade.filtertransformers.base_transformer.Quantity]'s to

    * do some semantic checks,
    * map quantities to the underlying backend field name.

    Attributes:
        name: The name of the quantity as used in the filter expressions.
        backend_field: The name of the field for this quantity in the backend database, will be
            `name` by default.
        length_quantity: Another (typically integer) [`Quantity`][optimade.filtertransformers.base_transformer.Quantity]
            that can be queried as the length of this quantity, e.g. `elements` and `nelements`. Backends
            can then decide whether to use this for all "LENGTH" queries.

    """

    name: str
    backend_field: Optional[str]
    length_quantity: Optional["Quantity"]

    def __init__(
        self,
        name: str,
        backend_field: str = None,
        length_quantity: "Quantity" = None,
    ):
        """Initialise the `quantity` from it's name and aliases.

        Parameters:
            name: The name of the quantity as used in the filter expressions.
            backend_field: The name of the field for this quantity in the backend database, will be
                `name` by default.
            length_quantity: Another (typically integer) [`Quantity`][optimade.filtertransformers.base_transformer.Quantity]
                that can be queried as the length of this quantity, e.g. `elements` and `nelements`. Backends
                can then decide whether to use this for all "LENGTH" queries.

        """

        self.name = name
        self.backend_field = backend_field if backend_field is not None else name
        self.length_quantity = length_quantity


class BaseTransformer(abc.ABC, Transformer):
    """Generic filter transformer that handles various
    parts of the grammar in a backend non-specific way.

    Attributes:
        operator_map: A map from comparison operators
            to their backend-specific versions.
        mapper: A resource mapper object that defines the
            expected fields and acts as a container for
            various field-related configuration.

    """

    mapper: Optional[BaseResourceMapper] = None
    operator_map: Dict[str, str] = {
        "<": None,
        "<=": None,
        ">": None,
        ">=": None,
        "!=": None,
        "=": None,
    }

    # map from operators to their syntactic (as opposed to logical) inverse to handle
    # equivalence between cases like "A > 3" and "3 < A".
    _reversed_operator_map = {
        ">": "<",
        ">=": "<=",
        "<": ">",
        "<=": ">=",
        "=": "=",
        "!=": "!=",
    }

    _quantity_type: Type[Quantity] = Quantity
    _quantities = None

    def __init__(
        self, mapper: BaseResourceMapper = None
    ):  # pylint: disable=super-init-not-called
        """Initialise the transformer object, optionally loading in a
        resource mapper for use when post-processing.

        """
        self.mapper = mapper

    @property
    def backend_mapping(self) -> Dict[str, Quantity]:
        """A mapping between backend field names (aliases) and the corresponding
        [`Quantity`][optimade.filtertransformers.base_transformer.Quantity] object.
        """
        return {
            quantity.backend_field: quantity for _, quantity in self.quantities.items()
        }

    @property
    def quantities(self) -> Dict[str, Quantity]:
        """A mapping from the OPTIMADE field name to the corresponding
        [`Quantity`][optimade.filtertransformers.base_transformer.Quantity] objects.
        """
        if self._quantities is None:
            self._quantities = self.__build_quantities()

        return self._quantities

    @quantities.setter
    def __set_quantities(self, quantities: Dict[str, Quantity]) -> None:
        self._quantities = quantities

    def __build_quantities(self) -> Dict[str, Quantity]:
        """Creates a dictionary of field names mapped to
        [`Quantity`][optimade.filtertransformers.base_transformer.Quantity] objects from the
        fields registered by the mapper.

        """

        quantities = {}

        if self.mapper is not None:
            for field in self.mapper.ALL_ATTRIBUTES:
                alias = self.mapper.get_backend_field(field)
                # Allow length aliases to be defined relative to either backend fields or OPTIMADE fields,
                # with preference for those defined from OPTIMADE fields
                length_alias = self.mapper.length_alias_for(
                    field
                ) or self.mapper.length_alias_for(alias)

                if field not in quantities:
                    quantities[field] = self._quantity_type(
                        name=field, backend_field=alias
                    )

                if length_alias:
                    if length_alias not in quantities:
                        quantities[length_alias] = self._quantity_type(
                            name=length_alias,
                            backend_field=self.mapper.get_backend_field(length_alias),
                        )
                    quantities[field].length_quantity = quantities[length_alias]

        return quantities

    def postprocess(self, query) -> Any:
        """Post-process the query according to the rules defined for
        the backend, returning the backend-specific query.

        """
        return query

    def transform(self, tree: Tree) -> Any:
        """Transform the query using the Lark `Transformer` then run the
        backend-specific post-processing methods.

        """
        return self.postprocess(super().transform(tree))

    def __default__(self, data, children, meta):
        """The default rule to call when no definition is found for a particular construct."""
        raise NotImplementedError(
            f"Calling __default__, i.e., unknown grammar concept. data: {data}, children: {children}, meta: {meta}"
        )

    def filter(self, arg):
        """filter: expression*"""
        return arg[0] if arg else None

    @v_args(inline=True)
    def constant(self, value):
        """constant: string | number"""
        # Note: Return as is.
        return value

    @v_args(inline=True)
    def value(self, value):
        """value: string | number | property"""
        # Note: Return as is.
        return value

    @v_args(inline=True)
    def non_string_value(self, value):
        """non_string_value: number | property"""
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

    def property(self, args: list) -> Any:
        """property: IDENTIFIER ( "." IDENTIFIER )*

        If this transformer has an associated mapper, the property
        will be compared to possible relationship entry types and
        for any supported provider prefixes. If there is a match,
        this rule will return a string and not a dereferenced
        [`Quantity`][optimade.filtertransformers.base_transformer.Quantity].

        Raises:
            BadRequest: If the property does not match any
                of the above rules.

        """
        quantity_name = str(args[0])

        # If the quantity name matches an entry type (indicating a relationship filter)
        # then simply return the quantity name; the inherited property
        # must then handle any further nested identifiers
        if self.mapper:
            if quantity_name in self.mapper.RELATIONSHIP_ENTRY_TYPES:
                return quantity_name

        if self.quantities and quantity_name not in self.quantities:
            # If the quantity is provider-specific, but does not match this provider,
            # then return the quantity name such that it can be treated as unknown.
            # If the prefix does not match another known provider, also emit a warning
            # If the prefix does match a known provider, do not return a warning.
            # Following [Handling unknown property names](https://github.com/Materials-Consortia/OPTIMADE/blob/master/optimade.rst#handling-unknown-property-names)
            if self.mapper and quantity_name.startswith("_"):
                prefix = quantity_name.split("_")[1]
                if not any(prefix == p for p in self.mapper.SUPPORTED_PREFIXES):
                    if not any(
                        prefix == p for p in self.mapper.KNOWN_PROVIDER_PREFIXES
                    ):
                        warnings.warn(
                            UnknownProviderProperty(
                                f"Field {quantity_name!r} has an unrecognised prefix: this property has been treated as UNKNOWN."
                            )
                        )

                    return quantity_name

            raise BadRequest(
                detail=f"'{quantity_name}' is not a known or searchable quantity"
            )

        quantity = self.quantities.get(quantity_name, None)
        if quantity is None:
            quantity = self._quantity_type(name=str(quantity_name))

        return quantity

    @v_args(inline=True)
    def string(self, string):
        """string: ESCAPED_STRING"""
        return string.strip('"')

    @v_args(inline=True)
    def signed_int(self, number):
        """signed_int : SIGNED_INT"""
        return int(number)

    @v_args(inline=True)
    def number(self, number):
        """number: SIGNED_INT | SIGNED_FLOAT"""
        if number.type == "SIGNED_INT":
            type_ = int
        elif number.type == "SIGNED_FLOAT":
            type_ = float
        return type_(number)

    @v_args(inline=True)
    def comparison(self, value):
        """comparison: constant_first_comparison | property_first_comparison"""
        # Note: Return as is.
        return value

    def value_list(self, arg):
        """value_list: [ OPERATOR ] value ( "," [ OPERATOR ] value )*"""

    def value_zip(self, arg):
        """value_zip: [ OPERATOR ] value ":" [ OPERATOR ] value (":" [ OPERATOR ] value)*"""
        pass

    def value_zip_list(self, arg):
        """value_zip_list: value_zip ( "," value_zip )*"""

    def expression(self, arg):
        """expression: expression_clause ( OR expression_clause )"""

    def expression_clause(self, arg):
        """expression_clause: expression_phrase ( AND expression_phrase )*"""

    def expression_phrase(self, arg):
        """expression_phrase: [ NOT ] ( comparison | "(" expression ")" )"""

    def property_first_comparison(self, arg):
        """property_first_comparison:
        property ( value_op_rhs
                 | known_op_rhs
                 | fuzzy_string_op_rhs
                 | set_op_rhs
                 | set_zip_op_rhs
                 | length_op_rhs )

        """

    def constant_first_comparison(self, arg):
        """constant_first_comparison: constant OPERATOR ( non_string_value | not_implemented_string )"""

    @v_args(inline=True)
    def value_op_rhs(self, operator, value):
        """value_op_rhs: OPERATOR value"""

    def known_op_rhs(self, arg):
        """known_op_rhs: IS ( KNOWN | UNKNOWN )"""

    def fuzzy_string_op_rhs(self, arg):
        """fuzzy_string_op_rhs: CONTAINS value | STARTS [ WITH ] value | ENDS [ WITH ] value"""

    def set_op_rhs(self, arg):
        """set_op_rhs: HAS ( [ OPERATOR ] value | ALL value_list | ANY value_list | ONLY value_list )"""

    def length_op_rhs(self, arg):
        """length_op_rhs: LENGTH [ OPERATOR ] value"""

    def set_zip_op_rhs(self, arg):
        """set_zip_op_rhs: property_zip_addon HAS ( value_zip
        | ONLY value_zip_list
        | ALL value_zip_list
        | ANY value_zip_list )

        """

    def property_zip_addon(self, arg):
        """property_zip_addon: ":" property (":" property)*"""
