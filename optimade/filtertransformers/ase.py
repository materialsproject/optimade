from typing import Tuple

from lark import Transformer

ASEQueryTree = Tuple  # return type of ASETransformer.transform()


class ASETransformer(Transformer):
    """Transform Lark-tree to simpler data-structure."""

    def filter(self, arg):
        return arg[0]

    def expression(self, arg):
        return arg[0]

    def expression_clause(self, args):
        if len(args) == 1:
            return args[0]
        return "AND", args

    def expression_phrase(self, arg):
        return arg[0]

    def comparison(self, arg):
        return arg[0]

    def property_first_comparison(self, args):
        return tuple(args)

    def property(self, args):
        return str(args[0])

    def value_op_rhs(self, args):
        op, rhs = args
        return str(op), rhs

    def value(self, args):
        return args[0]

    def number(self, args):
        (val,) = args
        return int(val)

    def set_op_rhs(self, args):
        op, rhs = args
        return str(op), rhs

    def string(self, args):
        return str(args[0])
