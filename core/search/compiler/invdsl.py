from parsley import wrapGrammar

from ometa.grammar import OMeta
from ometa.runtime import OMetaBase

from core.search.compiler.invparsley import grammar

name = 'InvDSL'
B = OMeta.makeGrammar(grammar, name=name).createParserClass(
    OMetaBase, globals()
)


class ICompiler(B):
    def directive(self, d, v):
        raise NotImplemented()

    def regexpr(self, r):
        raise NotImplemented()

    def text(self, t):
        raise NotImplemented()

    def compile(self, initial, values):
        raise NotImplemented()

    def OR_op(self, a, b):
        raise NotImplemented()

    def AND_op(self, a, b):
        raise NotImplemented()

    def NOT_op(self, a):
        raise NotImplemented()


class DebugCompiler(ICompiler):
    def directive(self, d, v):
        return d, v

    def regexpr(self, r):
        return r

    def text(self, t):
        return t

    def compile(self, initial, values):
        ret = initial
        for op, value in values:
            ret = op(ret, value)
        return ret

    def OR_op(self):
        return lambda a, b: '({0} {1} {2})'.format(a, 'OR', b)

    def AND_op(self):
        return lambda a, b: '({0} {1} {2})'.format(a, 'AND', b)

    def NOT_op(self):
        return lambda a: '({0} {1})'.format('NOT', a)


def make_debug_compiler():
    return wrapGrammar(DebugCompiler)
