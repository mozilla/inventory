import re
import pdb

"""
<stmt>  -> <term> <stmt>
<term>  -> <un> <word>
        -> <un> <op>:<list>
<list>  -> <word>, <list>
        -> <word>
<un>    -> ''|'-'
<word>  -> letters and stuff
"""

def parse_statement(ll, args):
    term = parse_term(ll)
    if term:
        args.append(term)
        parse_statement(ll, args)

def parse(ss):
    l = Lexer(ss)
    args = []
    parse_statement(l, args)
    return args


def parse_term(ll):
    word = ll.lex()
    if not word:
        return None
    word = word.strip(' ')
    if word.startswith('-'):
        un = 'exc'
        word = word[1:]
    else:
        un = 'inc'

    op = ""
    has_list = False
    for c in word:
        op += c
        if c == ':':
            has_list = True
            break

    if has_list:
        # Go back until the ':'
        while True:
            c = ll.peek()
            if c == ":":
                ll.pop()
                break
            else:
                ll.unpop()
        args = parse_list(ll)
    else:
        args = [op]
        op = "text:"

    pdb.set_trace()
    ex_args = expand_args(args)
    return (un, op, ex_args)

def expand_args(args):
    """
    Apply any macro expansion on args.
    Supported expansions (In order of application):

        1) x1..3 == x1 x2 x3
    """
    args = expand_range(args)
    return args

def expand_range(args):
    regex = re.compile("((\d+)\.\.(\d+))")
    new_args = []
    for arg in args:
        r = regex.search(arg)
        if r:
            rs = r.groups()[0]
        else:
            new_args.append(arg)
            continue
        new_arg = arg.replace(rs, "{0}")
        start = int(r.groups()[1])
        stop = int(r.groups()[2])
        if start > stop:
            return args
        for i in range(start, stop+1):
            new_args.append(new_arg.format(i))

    return new_args

def parse_list(ll, extra=None):
    args = []
    has_more = True

    arg = ""
    list_str = ""

    seen_comma = False
    seen_term = False
    while True:
        c = ll.pop()
        if c is None:
            break
        if not seen_term:
            if c == " ":
                continue
            if c == ",":
                continue
            seen_term = True
            list_str += c
            continue
        if not seen_comma:
            if c == " ":
                # Make sure we are not at the end of the list.
                if _is_list_end:
                    break
        if c == ',':
            seen_comma = False
            seen_term = False
        list_str += c
    return list_str.split(',')

def _is_list_end(ll):
    i = 0
    while True:
        c = ll.peekn(i)
        i += 1
        if c == ' ':
            continue
        elif c == ',':
            return False
        else:
            return True


def _lex_word(ll):
    word = ''
    while True:
        # Read in name
        c = ll.pop()
        if c is None:
            if word:
                return word
            else:
                return None
        if re.match('\s', c):
            ll.unpop()
            break
        else:
            word = word + c
    return word


def _lex_ws(ll):
    while True:
        # Read in name
        c = ll.pop()
        if c is None:
            return
        if re.match('\s', c):
            continue
        else:
            ll.unpop()
            break
    return

class Lexer(object):
    def __init__(self, line):
        self.line = line
        self.length = len(line)
        self.pos = 0

    def pop(self):
        if self.pos == self.length:
            return None
        else:
            c = self.line[self.pos]
            self.pos += 1
            return c

    def unpop(self):
        if self.pos > 0:
            self.pos -= 1

    def peek(self):
        if self.pos >= self.length:
            return None
        return self.line[self.pos]

    def peekn(self, n):
        if self.pos + n > self.length - 1:
            return None
        return self.line[self.pos+n]

    def lex(self):
        _lex_ws(self)
        return _lex_word(self)


"""
Some example searches:

foo vlan:22
webnode vlan:db site:scl4
webnode3..55
vlan:33 site:phx1.corp
vlan:33 site:corp.phx1
vld.dmz.mozilla.com
vld.dmz.mozilla.com type:CNAME,A, PTR
vld.dmz.mozilla.com type:CNAME/A/PTR

Operators:

vlan: <vlan_number>|<vlan_name> [, <vlan_number>|<vlan_name> ... ]
site: <site_name> [, <site_name> ... ]
type: <DNS Record Type>|Interface|Intr|System [, <DNS Record Type>|Interface|Intr|System .. ]

The '-' Not Operator (Excludes)

The '..' operator. Expands '1..4' to 4 different searches.
sys.exit()
print '---'
ss = "webnode vlan:db,dmz site:scl4"
print ss
print parse(ss)

print '---'
ss = "webnode -vlan:db,dmz -site:scl4"
print ss
print parse(ss)

print
print '---'
ss = "webnode vlan: site:scl4"
print ss
print parse(ss)

print
print '---'
ss = "-webnode vlan: site:scl4"
print ss
print parse(ss)

print
print '---'
ss = "webnode vlan:site:scl4"
print ss
print parse(ss)

print
print '---'
ss = "webnode vlan:site:scl4"
print ss
print parse(ss)

print
print '---'
ss = "v:s,y z:a, er asdf -dfddf"
print ss
print parse(ss)
"""
ss = "vlan:x1..100d"
print ss
print parse(ss)
