import re
import pdb


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
        self._lex_ws()
        return self._lex_token()

    def _lex_token(self):
        token = ''
        if self.peek() == ')':
            self.pop()
            return ')'
        if self.peek() == '-':
            self.pop()
            return '-'
        while True:
            # Read in name
            c = self.pop()
            if c is None:
                if token:
                    return token
                else:
                    return None
            if re.match('\s', c):
                self.unpop()
                break
            if c == ')':
                self.unpop()
                break
            if c == '(':
                token = token + c
                break
            else:
                token = token + c
        return token

    def _peek_token(self):
        token = ''
        i = 0
        while True:
            # Read in name
            c = self.peekn(i)
            i += 1
            if c is None:
                if token:
                    return token
                else:
                    return None
            if re.match('\s', c):
                break
            else:
                token = token + c
        return token


    def _lex_ws(self):
        while True:
            # Read in name
            c = self.pop()
            if c is None:
                return
            if re.match('\s', c):
                continue
            else:
                self.unpop()
                break
        return

def lex_stmt(ss):
    print ss
    ll = Lexer(ss)
    terms = []
    while True:
        term = ll.lex()
        if not term:
            break
        else:
            terms.append(term)
    return terms


if __name__ == "__main__":
    ss = "(foo)"
    print lex_stmt(ss)
    ss = "webnode vlan:db,dmz site:scl4"
    print lex_stmt(ss)

    print '---'
    ss = "webnode -vlan:db,dmz -site:scl4"
    print lex_stmt(ss)

    print
    print '---'
    ss = "webnode vlan: site:scl4"
    print lex_stmt(ss)

    print
    print '---'
    ss = "-webnode vlan: site:scl4"
    print lex_stmt(ss)

    print
    print '---'
    ss = "-webnode vlan: site:"
    print lex_stmt(ss)

    print
    print '---'
    ss = "webnode vlan:site:scl4"
    print lex_stmt(ss)

    print
    print '---'
    ss = "webnode vlan:site:scl4"
    print lex_stmt(ss)

    print
    print '---'
    ss = "v:s,y z:a, er asdf -dfddf"
    print lex_stmt(ss)

    print
    print '---'
    ss = "(v:s,y z:a,) er asdf -dfddf"
    print lex_stmt(ss)

    print
    print '---'

    ss = '"fooo"'
    ss = "foo: bar: baz"
    print lex_stmt(ss)

    ss = '"fooo"'
    ss = "() ()(bar ()(foo))baz"
    print lex_stmt(ss)

