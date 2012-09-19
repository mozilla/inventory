import re
import pdb
from copy import deepcopy
from tokenizer import Tokenizer
from utils import *

"""
<stmt>  -> <term> <stmt>
<term>  -> <un> <word>
        -> <un> <op>:<list>
<list>  -> <word>, <list>
        -> <word>
<un>    -> ''|'-'
<word>  -> letters and stuff
"""

class Node(object):
    def __init__(self, token, indent=0):
        self.token = token
        self.indent = indent
        self.r_child = None
        self.l_child = None

    def inline_print(self):
        if not (self.l_child or self.r_child):
            if self.token.value:
                print self.token.value,
        else:
            print '(',
            if self.l_child:
                self.l_child.inline_print()
            if self.token.value:
                print self.token.value,
            if self.r_child:
                self.r_child.inline_print()
            print ')',

    def rpn_print(self):
        if not (self.l_child or self.r_child):
            if self.token.value:
                print self.token.value,
        else:
            if self.l_child:
                self.l_child.rpn_print()
            if self.r_child:
                self.r_child.rpn_print()
            if self.token.value:
                print self.token.value,



    def inline_print(self):
        if not (self.l_child or self.r_child):
            print self.token.value,
        else:
            print '(',
            if self.l_child:
                self.l_child.inline_print()
            print self.token.value,
            if self.r_child:
                self.r_child.inline_print()
            print ')',

    def tree_print(self):
        print '\t'*self.indent + self.token

    def __str__(self):
        return str(self.token)

    def __repr__(self):
        return str(self)

def do_parse(ss):
    print ss
    p = Parser(ss)
    root_node = p.parse()
    root_node.inline_print()

class Parser(object):
    def __init__(self, stmt):
        # We always wrap with ()'s
        self.tnz = Tokenizer('('+stmt+')')

    def pop(self):
        return self.tnz.pop()

    def peek(self):
        return self.tnz.peek()

    def top(self):
        return self.tnz.top()

    def parse(self, indent=0):
        indent = deepcopy(indent)
        indent += 1
        if istype(self.top(), 'Lparen'):
            self.pop() # Open paren
            n = self.parse(indent)
            cp = self.pop() # Close paren
            if istype(self.top(), 'Bop'):
                bopr = Node(self.pop(), indent)
                bopr.l_child = n
                bopr.r_child = self.parse(indent)
                return bopr
            else:
                return n
        if istype(self.top(), 'Term'):
            if istype(self.peek(), 'Bop'):
                t1 = Node(self.pop(), indent)
                bopr = Node(self.pop(), indent)
                bopr.l_child = t1
                if istype(self.top(), 'Term'):
                    bopr.r_child = self.parse(indent)
                elif istype(self.top(), 'Lparen'):
                    bopr.r_child = self.parse(indent)
                else:
                    raise SyntaxError("Expected Term or (")
                return bopr
            elif istype(self.peek(), 'Rparen'):
                t1 = Node(self.pop(), indent)
                return t1
            elif istype(self.peek(), 'Term'):
                t1 = Node(self.pop(), indent)
                return t1
            else:
                raise SyntaxError("Expecting term or (")


if __name__ == "__main__":
    ss = "(foo)"
    print do_parse(ss)
    ss = "webnode vlan:db,dmz site:scl4"
    print do_parse(ss)

    print '---'
    ss = "webnode -vlan:db,dmz -site:scl4"
    print do_parse(ss)

    print
    print '---'
    ss = "webnode vlan: site:scl4"
    print do_parse(ss)

    print
    print '---'
    ss = "-webnode vlan: site:scl4"
    print do_parse(ss)

    print
    print '---'
    ss = "-webnode vlan: site:"
    print do_parse(ss)

    print
    print '---'
    ss = "webnode vlan:site:scl4"
    print do_parse(ss)

    print
    print '---'
    ss = "webnode vlan:site:scl4"
    print do_parse(ss)

    print
    print '---'
    ss = "v:s,y z:a, er asdf -dfddf"
    print do_parse(ss)

    print
    print '---'
    ss = "(v:s,y z:a,) er asdf -dfddf"
    print do_parse(ss)

    print
    print '---'

    ss = '"fooo"'
    ss = "foo: bar: baz"
    print do_parse(ss)
    print
    print '---'
