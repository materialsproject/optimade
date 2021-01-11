import copy
from lark import v_args, Token
from optimade.filtertransformers.base_transformer import BaseTransformer
from optimade.server.exceptions import BadRequest

__all__ = ("MongoTransformer",)


class MongoTransformer(BaseTransformer):
    """Transformer for MongoDB backend. Parses lark tree into
    a dictionary to be passed to pymongo/mongomock. Uses
    post-processing functions to handle aliasing and some
    specific edge-cases for MongoDB.

    """

    operator_map = {
        "<": "$lt",
        "<=": "$lte",
        ">": "$gt",
        ">=": "$gte",
        "!=": "$ne",
        "=": "$eq",
    }
    reversed_operator_map = {
        "$lt": "$gt",
        "$lte": "$gte",
        "$gt": "$lt",
        "$gte": "$lte",
        "$ne": "$ne",
        "$eq": "$eq",
    }

    def postprocess(self, query):
        """ Used to post-process the final parsed query. """
        if self.mapper:
            # important to apply length alias before normal aliases
            query = self._apply_length_aliases(query)
            query = self._apply_aliases(query)

        query = self._apply_relationship_filtering(query)
        query = self._apply_length_operators(query)
        query = self._apply_unknown_or_null_filter(query)
        query = self._apply_mongo_id_filter(query)

        return query

    def value_list(self, arg):
        # value_list: [ OPERATOR ] value ( "," [ OPERATOR ] value )*
        # NOTE: no support for optional OPERATOR, yet, so this takes the
        # parsed values and returns an error if that is being attempted
        for value in arg:
            if str(value) in self.operator_map.keys():
                raise NotImplementedError(
                    f"OPERATOR {value} inside value_list {arg} not implemented."
                )

        return arg

    def value_zip(self, arg):
        # value_zip: [ OPERATOR ] value ":" [ OPERATOR ] value (":" [ OPERATOR ] value)*
        raise NotImplementedError

    def value_zip_list(self, arg):
        # value_zip_list: value_zip ( "," value_zip )*
        raise NotImplementedError

    def expression(self, arg):
        # expression: expression_clause ( OR expression_clause )
        # expression with and without 'OR'
        return {"$or": arg} if len(arg) > 1 else arg[0]

    def expression_clause(self, arg):
        # expression_clause: expression_phrase ( AND expression_phrase )*
        # expression_clause with and without 'AND'
        return {"$and": arg} if len(arg) > 1 else arg[0]

    def expression_phrase(self, arg):
        # expression_phrase: [ NOT ] ( comparison | "(" expression ")" )
        return self._recursive_expression_phrase(arg)

    def property_first_comparison(self, arg):
        # property_first_comparison: property ( value_op_rhs | known_op_rhs | fuzzy_string_op_rhs | set_op_rhs |
        # set_zip_op_rhs | length_op_rhs )
        return {arg[0]: arg[1]}

    def constant_first_comparison(self, arg):
        # constant_first_comparison: constant OPERATOR ( non_string_value | not_implemented_string )
        return {arg[2]: {self.reversed_operator_map[self.operator_map[arg[1]]]: arg[0]}}

    @v_args(inline=True)
    def value_op_rhs(self, operator, value):
        # value_op_rhs: OPERATOR value
        return {self.operator_map[operator]: value}

    def known_op_rhs(self, arg):
        # known_op_rhs: IS ( KNOWN | UNKNOWN )
        # The OPTIMADE spec also required a type comparison with null, this must be post-processed
        # so here we use a special key "#known" which will get replaced in post-processing with the
        # expanded dict
        return {"#known": arg[1] == "KNOWN"}

    def fuzzy_string_op_rhs(self, arg):
        # fuzzy_string_op_rhs: CONTAINS value | STARTS [ WITH ] value | ENDS [ WITH ] value

        # The WITH keyword may be omitted.
        if isinstance(arg[1], Token) and arg[1].type == "WITH":
            pattern = arg[2]
        else:
            pattern = arg[1]

        # CONTAINS
        if arg[0] == "CONTAINS":
            regex = f"{pattern}"
        elif arg[0] == "STARTS":
            regex = f"^{pattern}"
        elif arg[0] == "ENDS":
            regex = f"{pattern}$"
        return {"$regex": regex}

    def set_op_rhs(self, arg):
        # set_op_rhs: HAS ( [ OPERATOR ] value | ALL value_list | ANY value_list | ONLY value_list )

        if len(arg) == 2:
            # only value without OPERATOR
            return {"$in": arg[1:]}

        if arg[1] == "ALL":
            return {"$all": arg[2]}

        if arg[1] == "ANY":
            return {"$in": arg[2]}

        if arg[1] == "ONLY":
            return {"$all": arg[2], "$size": len(arg[2])}

        # value with OPERATOR
        raise NotImplementedError(
            f"set_op_rhs not implemented for use with OPERATOR. Given: {arg}"
        )

    def length_op_rhs(self, arg):
        # length_op_rhs: LENGTH [ OPERATOR ] value
        if len(arg) == 2 or (len(arg) == 3 and arg[1] == "="):
            return {"$size": arg[-1]}

        elif arg[1] in self.operator_map and arg[1] != "!=":
            # create an invalid query that needs to be post-processed
            # e.g. {'$size': {'$gt': 2}}, which is not allowed by Mongo.
            return {"$size": {self.operator_map[arg[1]]: arg[-1]}}

        raise NotImplementedError(
            f"Operator {arg[1]} not implemented for LENGTH filter."
        )

    def set_zip_op_rhs(self, arg):
        # set_zip_op_rhs: property_zip_addon HAS ( value_zip | ONLY value_zip_list | ALL value_zip_list |
        # ANY value_zip_list )
        raise NotImplementedError

    def property_zip_addon(self, arg):
        # property_zip_addon: ":" property (":" property)*
        raise NotImplementedError

    def _recursive_expression_phrase(self, arg):
        """Helper function for parsing `expression_phrase`. Recursively sorts out
        the correct precedence for `$and`, `$or` and `$nor`.

        """
        if len(arg) == 1:
            # without NOT
            return arg[0]

        # handle the case of {"$not": {"$or": [expr1, expr2]}} using {"$nor": [expr1, expr2]}.
        if "$or" in arg[1]:
            return {"$nor": self._recursive_expression_phrase([arg[1]["$or"]])}

        # handle the case of {"$not": {"$and": [expr1, expr2]}} using per-expression negation,
        # e.g. {"$and": [{prop1: {"$not": expr1}}, {prop2: {"$not": ~expr2}}]}.
        # Note that this is not the same as NOT (expr1 AND expr2)!
        if "$and" in arg[1]:
            return {
                "$and": [
                    self._recursive_expression_phrase(["NOT", subdict])
                    for subdict in arg[1]["$and"]
                ]
            }

        # simple case of negating one expression, from NOT (expr) to ~expr.
        return {prop: {"$not": expr} for prop, expr in arg[1].items()}

    def _apply_length_aliases(self, filter_: dict) -> dict:
        """Recursively search query for any `$size` operations, and check
        if the property can be replaced with its corresponding length
        alias.

        """

        def check_for_size(prop, expr):
            return (
                isinstance(expr, dict)
                and "$size" in expr
                and self.mapper.length_alias_for(prop)
            )

        def replace_with_length_alias(subdict, prop, expr):
            subdict[self.mapper.length_alias_for(prop)] = expr["$size"]
            subdict[prop].pop("$size")
            if not subdict[prop]:
                subdict.pop(prop)
            return subdict

        return recursive_postprocessing(
            filter_, check_for_size, replace_with_length_alias
        )

    def _apply_aliases(self, filter_: dict) -> dict:
        """Check whether any fields in the filter have aliases so
        that they can be renamed for the Mongo query.

        """
        # if there are no defined aliases, just skip
        if not self.mapper.all_aliases():
            return filter_

        def check_for_alias(prop, expr):
            return self.mapper.alias_for(prop) != prop

        def apply_alias(subdict, prop, expr):
            if isinstance(subdict, dict):
                subdict[self.mapper.alias_for(prop)] = self._apply_aliases(
                    subdict.pop(prop)
                )
            elif isinstance(subdict, str):
                subdict = self.mapper.alias_for(subdict)

            return subdict

        return recursive_postprocessing(filter_, check_for_alias, apply_alias)

    def _apply_length_operators(self, filter_: dict) -> dict:
        """Check for any invalid pymongo queries that involve
        applying an operator to the length of a field, and transform
        them into a test for existence of the relevant entry, e.g.
        "list LENGTH > 3" becomes "does the 4th list entry exist?".

        """

        def check_for_length_op_filter(prop, expr):
            return (
                isinstance(expr, dict)
                and "$size" in expr
                and isinstance(expr["$size"], dict)
            )

        def apply_length_op(subdict, prop, expr):
            # assumes that the dictionary only has one element by design
            # (we just made it above in the transformer)
            operator, value = list(expr["$size"].items())[0]
            if operator in self.operator_map.values() and operator != "$ne":
                # worth being explicit here, I think
                _prop = None
                existence = None
                if operator == "$gt":
                    _prop = f"{prop}.{value + 1}"
                    existence = True
                elif operator == "$gte":
                    _prop = f"{prop}.{value}"
                    existence = True
                elif operator == "$lt":
                    _prop = f"{prop}.{value}"
                    existence = False
                elif operator == "$lte":
                    _prop = f"{prop}.{value + 1}"
                    existence = False
                if _prop is not None:
                    subdict.pop(prop)
                    subdict[_prop] = {"$exists": existence}

            return subdict

        return recursive_postprocessing(
            filter_,
            check_for_length_op_filter,
            apply_length_op,
        )

    def _apply_relationship_filtering(self, filter_: dict) -> dict:
        """Check query for property names that match the entry
        types, and transform them as relationship filters rather than
        property filters.

        """

        def check_for_entry_type(prop, expr):
            return str(prop).count(".") == 1 and str(prop).split(".")[0] in (
                "structures",
                "references",
            )

        def replace_with_relationship(subdict, prop, expr):
            _prop, _field = str(prop).split(".")
            if _field != "id":
                raise NotImplementedError(
                    f'Cannot filter relationships by field "{_field}", only "id" is supported.'
                )

            # in the case of HAS ONLY, the size operator needs to be applied
            # one level up, i.e. excluding the field
            if "$size" in expr:
                if "$and" not in subdict:
                    subdict["$and"] = []
                subdict["$and"].extend(
                    [
                        {f"relationships.{_prop}.data": {"$size": expr.pop("$size")}},
                        {f"relationships.{_prop}.data.{_field}": expr},
                    ]
                )
            else:
                subdict[f"relationships.{_prop}.data.{_field}"] = expr

            subdict.pop(prop)

            return subdict

        return recursive_postprocessing(
            filter_, check_for_entry_type, replace_with_relationship
        )

    def _apply_unknown_or_null_filter(self, filter_: dict) -> dict:
        """This method loops through the query and replaces the check for
        KNOWN with a check for existence and a check for not null, and the
        inverse for UNKNOWN.

        """

        def check_for_known_filter(_, expr):
            """Find cases where the query dict looks like
            `{"field": {"#known": T/F}}` or
            `{"field": "$not": {"#known": T/F}}`, which is a magic word
            for KNOWN/UNKNOWN filters in this transformer.

            """
            return isinstance(expr, dict) and (
                "#known" in expr or "#known" in expr.get("$not", {})
            )

        def replace_known_filter_with_or(subdict, prop, expr):
            """Replace magic key `"#known"` (added by this transformer) with the appropriate
            combination of `$exists` and/or test for nullity.
            combination of $exists and/or $eq/$ne null.

            """
            not_ = set(expr.keys()) == {"$not"}
            if not_:
                expr = expr["$not"]

            exists = expr["#known"] ^ not_

            top_level_key = "$or"
            comparison_operator = "$eq"
            if exists:
                top_level_key = "$and"
                comparison_operator = "$ne"

            if top_level_key not in subdict:
                subdict[top_level_key] = []

            subdict[top_level_key].append({prop: {"$exists": exists}})
            subdict[top_level_key].append({prop: {comparison_operator: None}})

            subdict.pop(prop)

            return subdict

        return recursive_postprocessing(
            filter_, check_for_known_filter, replace_known_filter_with_or
        )

    def _apply_mongo_id_filter(self, filter_: dict) -> dict:
        """This method loops through the query and replaces any operations
        on the special Mongodb `_id` key with the corresponding operation
        on a BSON `ObjectId` type.
        """

        def check_for_id_key(prop, _):
            """ Find cases where the query dict is operating on the `_id` field. """
            return prop == "_id"

        def replace_str_id_with_objectid(subdict, prop, expr):
            from bson import ObjectId

            for operator in subdict[prop]:
                val = subdict[prop][operator]
                if operator not in ("$eq", "$ne"):
                    if self.mapper is not None:
                        prop = self.mapper.alias_of(prop)
                    raise BadRequest(
                        detail=f"Operator not supported for query on field {prop!r}, can only test for equality"
                    )
                if isinstance(val, str):
                    subdict[prop][operator] = ObjectId(val)
            return subdict

        return recursive_postprocessing(
            filter_, check_for_id_key, replace_str_id_with_objectid
        )


def recursive_postprocessing(filter_, condition, replacement):
    """Recursively descend into the query, checking each dictionary
    (contained in a list, or as an entry in another dictionary) for
    the condition passed. If the condition is true, apply the
    replacement to the dictionary.

    Parameters:
        filter_ (list/dict): the filter_ to process.
        condition (callable): a function that returns True if the
            replacement function should be applied. It should take
            as arguments the property and expression from the filter_,
            as would be returned by iterating over `filter_.items()`.
        replacement (callable): a function that returns the processed
            dictionary. It should take as arguments the dictionary
            to modify, the property and the expression (as described
            above).

    Example:
        For the simple case of replacing one field name with
        another, the following functions could be used:

        ```python
        def condition(prop, expr):
            return prop == "field_name_old"

        def replacement(d, prop, expr):
            d["field_name_old"] = d.pop(prop)

        filter_ = recursive_postprocessing(
            filter_, condition, replacement
        )

        ```

    """
    if isinstance(filter_, list):
        result = [recursive_postprocessing(q, condition, replacement) for q in filter_]
        return result

    if isinstance(filter_, dict):
        # this could potentially lead to memory leaks if the filter_ is *heavily* nested
        _cached_filter = copy.deepcopy(filter_)
        for prop, expr in filter_.items():
            if condition(prop, expr):
                _cached_filter = replacement(_cached_filter, prop, expr)
            elif isinstance(expr, list):
                _cached_filter[prop] = [
                    recursive_postprocessing(q, condition, replacement) for q in expr
                ]
        return _cached_filter

    return filter_
