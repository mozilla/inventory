from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db.models import Q

from mozdns.address_record.models import AddressRecord
from mozdns.cname.models import CNAME
from mozdns.domain.models import Domain
from mozdns.mx.models import MX
from mozdns.nameserver.models import Nameserver
from mozdns.ptr.models import PTR
from mozdns.srv.models import SRV
from mozdns.sshfp.models import SSHFP
from mozdns.txt.models import TXT

from core.interface.static_intr.models import StaticInterface
from core.site.models import Site
from core.vlan.models import Vlan
from core.utils import two_to_four, IPFilter

from systems.models import System

from lexer import Lexer
import re
import pdb
import ipaddr

PR_UOP = 0
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
    # Alphabetical order
    q_sets = [
        build_filter(f, AddressRecord.search_fields),
        build_filter(f, CNAME.search_fields),
        build_filter(f, Domain.search_fields),
        build_filter(f, MX.search_fields),
        build_filter(f, Nameserver.search_fields),
        build_filter(f, PTR.search_fields),
        build_filter(f, SRV.search_fields),
        build_filter(f, SSHFP.search_fields),
        build_filter(f, StaticInterface.search_fields),
        build_filter(f, System.search_fields),
        build_filter(f, TXT.search_fields)
        ]
    return q_sets


def build_ipf_qsets(qset):
    # Alphabetical order
    q_sets = [
        qset,  # AddressRecord
        None,
        None,
        None,
        None,
        qset,  # PTR
        None,
        None,
        qset,  # StaticInterface
        None,
        None
        ]
    return q_sets

def build_rdtype_qsets(rdtype):
    """This function needs to filter out all records of a certain rdtype (like
    A or CNAME). Any filter produced here has to be able to be negated. We use
    the fact that every object has a pk > -1. When a qset is negated the query
    becomes pk <= -1.
    """
    rdtype = rdtype.upper()  # Let's get consistent
    select = Q(pk__gt=-1)
    no_select = Q(pk__lte=-1)
    q_sets = [
        select if rdtype == 'A' else no_select,
        select if rdtype == 'CNAME' else no_select,
        select if rdtype == 'DOMAIN' else no_select,
        select if rdtype == 'MX' else no_select,
        select if rdtype == 'NS' else no_select,
        select if rdtype == 'PTR' else no_select,
        select if rdtype == 'SRV' else no_select,
        select if rdtype == 'SSHFP' else no_select,
        select if rdtype == 'INTR' else no_select,
        select if rdtype == 'SYSTEM' else no_select,
        select if rdtype == 'TXT' else no_select
        ]
    return q_sets



class Token(object):
    def __init__(self, type_, value, precedence, col):
        self.value = value.strip()
        self.type_ = type_.title()
        self.precedence = precedence
        self.col = col
        self.types = [
                ('directive', re.compile("^(.*)=:(.*?)$")), # type, vlan, etc
                # It can't be ':' because ipv6 addresses use it
                ('text', re.compile("^(.*)$")), # Default to term
            ]

    def __str__(self):
        return "{0} {1}".format(self.type_, self.value)

    def __repr__(self):
        return str(self)

    def compile_Q(self):
        # Depending on the matched type, build the correct q set
        return build_text_qsets(self.value)

class BadDirective(Exception):
    pass

class DirectiveToken(Token):
    def __init__(self, type_, directive, value, precedence, col):
        self.directive = directive
        super(DirectiveToken, self).__init__(type_,
                value, precedence, col)

    def __str__(self):
        return "{0} {1}=:{2}".format(self.type_, self.directive, self.value)

    def compile_Q(self):
        if self.directive == 'network':
            if self.value.find(':') > -1:
                Klass = ipaddr.IPv6Network
                ip_type = '6'
            if self.value.find('.') > -1:
                Klass = ipaddr.IPv4Network
                ip_type = '4'
            try:
                network = Klass(self.value)
                ip_info = two_to_four(int(network.network),
                                      int(network.broadcast))
                ipf = IPFilter(None, ip_type, *ip_info)
            except (ipaddr.AddressValueError, ipaddr.NetmaskValueError), e:
                raise BadDirective("{0} isn't a valid "
                        "network.".format(self.value))
            return build_ipf_qsets(ipf.compile_Q())
        elif self.directive == 'type':
            return build_rdtype_qsets(self.value)
        elif self.directive == 'site':
            try:
                site = Site.objects.get(name=self.value)
            except ObjectDoesNotExist, e:
                raise BadDirective("{0} isn't a valid "
                        "site.".format(self.value))
            return build_ipf_qsets(site.compile_Q('4'))
        elif self.directive == 'vlan':
            try:
                if self.value.isdigit():
                    vlan = Vlan.objects.get(number=self.value)
                else:
                    vlan = Vlan.objects.get(name=self.value)
            except ObjectDoesNotExist, e:
                raise BadDirective("{0} isn't a valid "
                        "vlan identifier.".format(self.value))
            except MultipleObjectsReturned, e:
                raise BadDirective("{0} doesn't uniquely identify"
                        "a vlan.".format(self.value))
            return build_ipf_qsets(vlan.compile_Q('4'))
        else:
            raise BadDirective("Unknown directive "
                "'{0}'".format(self.directive))


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
        ('uop', re.compile("^(-)$"), PR_UOP), # NOT Unary Operator
        ('lparen', re.compile("^(\()$"), PR_LPAREN),  # Left paren
        ('rparen', re.compile("^(\))$"), PR_RPAREN), # Right paren
        ('bop', re.compile("(and)$", re.IGNORECASE), PR_AND), # AND Binary Operator
        ('bop', re.compile("(or)$", re.IGNORECASE), PR_OR), # OR Binary Operator
        ('directive', re.compile("^(.*)=:(.*?)$"), PR_TERM),
        ('term', re.compile("^(.*)$"), PR_TERM) # Everything else is a term
    ]

    def n(self):
        term = self.ll.lex()
        col = self.ll.pos
        if not term:
            return None
        for type_, pattern, precedence in self.patterns:
            match = pattern.match(term)
            if not match:
                continue
            if type_ == 'directive':
                # we need to make sure a trailing space doesn't through
                # us off.
                directive = match.groups(1)[0]
                value = match.groups(1)[1]
                if value:
                    return DirectiveToken(type_, directive, value, precedence,
                                          col)
                self.ll._lex_ws()
                nxt_token = self.ll.peek_token()
                for itype_, ipattern, iprecedence in self.patterns:
                    match = ipattern.match(nxt_token)
                    if not match:
                        continue
                    if itype_ == 'term':
                        value = self.ll.lex()  # we are eating this term
                        break
                    else:
                        break

                return DirectiveToken(type_, directive, value, precedence,
                                      col)
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
                    or (cur.type_ == 'Term' and nxt.type_ == 'Directive')
                    or (cur.type_ == 'Directive' and nxt.type_ == 'Term')
                    or (cur.type_ == 'Directive' and nxt.type_ == 'Directive')
                    or (cur.type_ in ('Term', 'Directive')
                        and nxt.type_ == 'Uop')
                    or (cur.type_ in ('Term', 'Directive')
                        and nxt.type_ == 'Lparen')
                    or (nxt.type_ in ('Term', 'Directive')
                        and cur.type_ == 'Rparen')):
                    new_tokens.append(cur)
                    new_tokens.append(Token('Bop', 'AND', PR_AND, cur.col))
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
    ss = "()"
    print print_tokens(ss)
    print
    print '---'

    ss = "(foo)"
    print print_tokens(ss)
    ss = "(webnode vlan=:db vlan=: foo site:scl4)"
    print print_tokens(ss)
    ss = "(site=: vlan=: db)"
    print print_tokens(ss)

    ss = "(site=:db)"
    print print_tokens(ss)

    """
    ss = "(-site=: db)"
    print print_tokens(ss)
