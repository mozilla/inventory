import pdb
import re
import ply.lex as lex
from core.search.compiler.invfilter import *


class InvLexer(object):

    tokens = ( 'NOT',
        'TEXT', 'DIRECTIVE', 'RE',
        'AND', 'OR',
        'LPAREN', 'RPAREN',
    )

    # Tokens
    t_LPAREN = r'\('
    t_RPAREN = r'\)'

    def t_NOT(self, t):
        r'\s*-'
        t.value = 'NOT'
        return t

    def t_AND(self, t):
        r'AND'
        return t

    def t_OR(self, t):
        r'OR'
        return t

    def t_DIRECTIVE(self, t):
        r'([a-zA-Z_]+)=:([a-zA-Z0-9_\./,:-]+)'
        r = r'([a-zA-Z_]+)=:([a-zA-Z0-9_\./:,-]+)'
        match = re.compile(r).match(t.value)
        directive = match.groups(1)[0]
        dvalue = match.groups(1)[1]
        t.value = DirectiveFilter(t.value, directive, dvalue)
        return t

    def t_RE(self, t):
        r'/\S+'
        r = r'/(\S+)'
        match = re.compile(r).match(t.value)
        rvalue = match.groups(1)[0]
        t.value = REFilter(rvalue)
        return t

    def t_TEXT(self, t):
        r'[a-zA-Z0-9_\.:-]+'
        t.value = TextFilter(t.value)
        return t

    # Ignored characters
    t_ignore = " \t"

    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += t.value.count("\n")

    def t_error(self, t):
        raise SyntaxError("Illegal character '%s'" % t.value[0])

    # Build the lexer
    def build_lexer(self, **kwargs):
        self.lexer = lex.lex(module=self, **kwargs)
