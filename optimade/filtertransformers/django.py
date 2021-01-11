import warnings

warnings.warn(
    "Django functionality is deprecated and will be removed in later versions (unless support is requested).",
    DeprecationWarning,
    stacklevel=2,
)

import operator
from optimade.filterparser import LarkParser
from lark import Tree
from lark.lexer import Token
from django.db.models import Q


__all__ = ("DjangoTransformer",)


class DjangoQueryError(Exception):
    pass


django_db_keys = {
    "natoms": "entry__natoms",
    "chemical_formula": "composition__formula__in",
    "stability": "stability",
    "band_gap": "calculation__band_gap",
    "element": "composition__element_list__contains",
    "nelements": "entry__composition__ntypes",
}


class DjangoTransformer:
    """Filter transformer for implementations using Django.

    !!! warning "Warning"
        This transformer is deprecated as it only supports
        the 0.9.7 grammar version, and works different to other
        filter transformers in this package.

    """

    def __init__(self):
        self.opers = {
            "=": self.eq,
            ">": self.gt,
            ">=": self.ge,
            "<": self.lt,
            "<=": self.le,
            "!=": self.ne,
            "OR": self.or_,
            "AND": self.and_,
            "NOT": self.not_,
        }
        self.parser = LarkParser(version=(0, 9, 7))

    def parse_raw_q(self, raw_query):
        return self.parser.parse(raw_query)

    def eq(self, a, b):
        return Q(**{a: b})

    def gt(self, a, b):
        return Q(**{a + "__gt": b})

    def ge(self, a, b):
        return Q(**{a + "__gte": b})

    def lt(self, a, b):
        return Q(**{a + "__lt": b})

    def le(self, a, b):
        return Q(**{a + "__lte": b})

    def ne(self, a, b):
        return ~Q(**{a: b})

    def not_(self, a):
        return ~a

    def and_(self, a, b):
        return operator.and_(a, b)

    def or_(self, a, b):
        return operator.or_(a, b)

    def evaluate(self, parse_Tree):
        if isinstance(parse_Tree, Tree):
            children = parse_Tree.children
            if len(children) == 1:
                return self.evaluate(children[0])
            elif len(children) == 2:
                op_fn = self.evaluate(children[0])
                return op_fn(self.evaluate(children[1]))
            elif len(children) == 3:
                if parse_Tree.data == "comparison":
                    db_prop = self.evaluate(children[0])
                    op_fn = self.evaluate(children[1])

                    if db_prop in django_db_keys.keys():
                        return op_fn(
                            django_db_keys[db_prop], self.evaluate(children[2])
                        )
                    else:
                        raise DjangoQueryError(
                            "Unknown property is queried : " + (db_prop)
                        )

                else:
                    op_fn = self.evaluate(children[1])
                    return op_fn(self.evaluate(children[0]), self.evaluate(children[2]))
            else:
                raise DjangoQueryError("Not compatible format. Tree has >3 children")

        elif isinstance(parse_Tree, Token):
            if parse_Tree.type == "VALUE":
                return parse_Tree.value
            elif parse_Tree.type in ["NOT", "CONJUNCTION", "OPERATOR"]:
                return self.opers[parse_Tree.value]
        else:
            raise DjangoQueryError("Not a Lark Tree or Token")
