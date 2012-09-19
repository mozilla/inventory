from django.db.models import Q

import mozdns
import core
from mozdns.address_record.models import AddressRecord
from mozdns.cname.models import CNAME
from mozdns.domain.models import Domain
from mozdns.mx.models import MX
from mozdns.nameserver.models import Nameserver
from mozdns.ptr.models import PTR
from mozdns.srv.models import SRV
from mozdns.sshfp.models import SSHFP
from core.interface.static_intr.models import StaticInterface
from mozdns.txt.models import TXT

from lexer import Lexer
import re
import pdb

PR_UOP = 1
PR_LPAREN = 2
PR_RPAREN = 2
PR_AND = 1
PR_OR = 2
PR_TERM = -1

def build_filter(filter_, fields, filter_type = "icontains"):
    # rtucker++
    final_filter = Q()
    if filter_ and filter_[0] == '/':
        filter_ = filter_[1:]
        filter_type = "regex"
    for t in fields:
        final_filter = final_filter | Q(**{"{0}__{1}".format(t,
            filter_type): filter_})

    return final_filter

def build_text_qsets(f):
    q_sets = []
    # Alphabetical order
    q_sets.append(build_filter(f, AddressRecord.search_fields))
    q_sets.append(build_filter(f, CNAME.search_fields))
    q_sets.append(build_filter(f, Domain.search_fields))
    q_sets.append(build_filter(f, MX.search_fields))
    q_sets.append(build_filter(f, Nameserver.search_fields))
    q_sets.append(build_filter(f, PTR.search_fields))
    q_sets.append(build_filter(f, SRV.search_fields))
    q_sets.append(build_filter(f, SSHFP.search_fields))
    q_sets.append(build_filter(f, StaticInterface.search_fields))
    q_sets.append(build_filter(f, TXT.search_fields))
    return q_sets

class Token(object):
    def __init__(self, type_, value, precedence, col):
        self.value = value
        self.type_ = type_.title()
        self.precedence = precedence
        self.col = col
        self.types = [
                ('directive', re.compile("^(.*):(.*)$")) # type, vlan, etc
                ('text', re.compile("^(.*)$")), # Default to term
            ]

    def __str__(self):
        return "{0} {1}".format(self.type_, self.value)

    def __repr__(self):
        return str(self)

    def compile_q(self):
        # Depending on the matched type, build the correct q set
        return build_text_qsets(self.value)


class Tokenizer(object):
    def __init__(self, stmt):
        self.ll = Lexer(stmt)
        self.tokens = []
        self._get_tokens()
        self.idx = 0

    def pop(self):
        try:
            token = self.tokens[self.idx]
            self.idx += 1
            return token
        except IndexError:
            return None

    def top(self):
        try:
            token = self.tokens[self.idx]
            return token
        except IndexError:
            return None

    def peek(self):
        try:
            token = self.tokens[self.idx+1]
            return token
        except IndexError:
            return None

    # List of types
    # Operators And precedence rules
    patterns = [
        ('uop', re.compile("^(!)$"), PR_UOP), # NOT Unary Operator
        ('lparen', re.compile("^(\()$"), PR_LPAREN),  # Left paren
        ('rparen', re.compile("^(\))$"), PR_RPAREN), # Right paren
        ('bop', re.compile("(and)$", re.IGNORECASE), PR_AND), # AND Binary Operator
        ('bop', re.compile("(or)$", re.IGNORECASE), PR_OR), # OR Binary Operator
        ('term', re.compile("^(.*)$"), PR_TERM) # Everything else is a term
    ]

    def n(self):
        term = self.ll.lex()
        col = self.ll.pos
        if not term:
            return None
        for type_, pattern, precedence in self.patterns:
            match = pattern.match(term)
            if match:
                if type_ == 'uop' or type_ == 'bop':
                    opr = match.groups(1)[0]
                    return Token(type_, opr.upper(), precedence, col)
                if type_ in ('lparen','rparen'):
                    paren = match.groups(1)[0]
                    return Token(type_, paren, precedence, col)
                if type_ == 'term':
                    term = match.groups(1)[0]
                    return Token(type_, term, precedence, col)

    def _get_tokens(self):
        first = True
        while True:
            token = self.n()
            if not token:
                self.tokens.append(None)
                break
            else:
                self.tokens.append(token)

        def add_ands(tokens):
            # When no operator exists we need to put an AND.
            new_tokens = []
            seen_term = False
            i = 0
            while i < (len(tokens) - 1):
                cur = tokens[i]
                nxt = tokens[i+1]
                if not nxt:
                    new_tokens.append(cur)
                    break

                if ((cur.type_ == 'Term' and nxt.type_ == 'Term')
                    or (cur.type_ == 'Term' and nxt.type_ == 'Lparen')
                    or (cur.type_ == 'Rparen' and nxt.type_ == 'Term')):
                    new_tokens.append(cur)
                    new_tokens.append(Token('Bop', 'AND', PR_AND, None))
                    i += 1
                else:
                    new_tokens.append(cur)
                    i += 1
            return new_tokens

        def add_parens(tokens):
            new_tokens = []
            for token in self.tokens:
                if token.precedence > -1:
                    if token.type_ == 'Lparen':
                        for i in xrange(token.precedence):
                            new_tokens.append(Token('Lparen', '(',
                                token.precedence, None))
                        new_tokens.append(token)
                        continue
                    elif token.type_ == 'Rparen':
                        for i in xrange(token.precedence):
                            new_tokens.append(Token('Rparen', ')',
                                token.precedence, None))
                        new_tokens.append(token)
                    else:
                        for i in xrange(token.precedence):
                            new_tokens.append(Token('Rparen', ')',
                                token.precedence, None))
                        new_tokens.append(token)
                        for i in xrange(token.precedence):
                            new_tokens.append(Token('Lparen', '(',
                                token.precedence, None))
                else:
                    new_tokens.append(token)
            return new_tokens



        self.tokens = add_ands(self.tokens)
        self.tokens = add_parens(self.tokens)




def print_tokens(ss):
    tokenizer = Tokenizer(ss)
    print ss
    print tokenizer.tokens

if __name__ == "__main__":
    """

    ss = "webnode OR vlan:db,dmz site:scl4"
    print print_tokens(ss)

    print '---'
    ss = "webnode -vlan:db,dmz -site:scl4"
    print print_tokens(ss)

    print
    print '---'
    ss = "webnode vlan: site:scl4"
    print print_tokens(ss)

    print
    print '---'
    ss = "-webnode vlan: site:scl4"
    print print_tokens(ss)

    print
    print '---'
    ss = "-webnode vlan: site:"
    print print_tokens(ss)

    print
    print '---'
    ss = "webnode vlan:site:scl4"
    print print_tokens(ss)

    print
    print '---'
    ss = "webnode vlan:site:scl4"
    print print_tokens(ss)

    print
    print '---'
    ss = "v:s,y z:a, er asdf -dfddf"
    print print_tokens(ss)

    print
    print '---'
    ss = "(v:s,y z:a,) er asdf -dfddf"
    print print_tokens(ss)

    print
    print '---'

    ss = '"fooo"'
    ss = "foo: bar: baz"
    print print_tokens(ss)
    print
    print '---'

    ss = '"fooo"'
    ss = "() ()(bar ()(foo))baz"
    print print_tokens(ss)
    print
    print '---'

    ss = "(a AND (b AND c) AND a)"
    print print_tokens(ss)
    print
    print '---'
    ss = "(a (b c) a)"
    print print_tokens(ss)
    print
    print '---'
    """
    ss = "()"
    print print_tokens(ss)
    print
    print '---'

    ss = "(foo)"
    print print_tokens(ss)
    ss = "(webnode vlan:db,dmz site:scl4)"
    print print_tokens(ss)
