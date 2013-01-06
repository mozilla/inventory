import re
import os


def get_serial(file_):
    """
    Retrieve the serial number of a zone.

    :param file_: The file with the SOA in it.
    :type file_: file
    """
    if not os.path.exists(file_):
        return ''
    with open(file_, 'r') as fd:
        return _str_get_serial(fd)

def _str_get_serial(text):
    """Read in a zone file and find the serial number.

    :param text: the zone file.
    :type text: A file-ish object (StringIO or actual file descriptor)
    :returns serial: The serial number
    :serial: str
    """
    # We already know it's in valid format.
    isSOA = False
    done = False
    for raw_line in text.readlines():
        if done:
            break

        line = raw_line.strip()
        ll = LexLine(line)
        if isSOA:
            # If we made it here, this should be the serial.
            serial = _lex_word(ll)
            if serial.isdigit():
                return serial
            else:
                return ''

        if not line or line[0] == '$' or line[0] == ';':
            continue

        # name        ttl class rr    name-server email-addr  (sn ref ret ex min)
        # 1           2   3     4     5           6            7  8   9   10 11
        # Everything up through 6 needs to be on the same line.
        _lex_word(ll)  # name
        _lex_ws(ll)

        c = ll.pop()
        if c.isdigit():
            _lex_word(ll)  # ttl
            _lex_ws(ll)
        else:
            ll.unpop()

        _lex_word(ll)  # class
        _lex_ws(ll)

        rr = _lex_word(ll)
        if rr.upper() != 'SOA':
            continue # It's not an soa, keep going.

        isSOA = True
        _lex_ws(ll)

        _lex_word(ll)  # ns
        _lex_ws(ll)

        email = _lex_word(ll)  # email
        if email[-1:] == '(':
            _lex_ws(ll)
        else:
            _lex_ws(ll)
            next = ll.peek()
            if next == '(':
                ll.pop()

        # We are into the numbers.
        _lex_ws(ll)
        serial = _lex_word(ll)
        if not serial:
            # The serial must be on the next line
            continue

        if serial.isdigit():
            return serial
        else:
            return ''

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


class LexLine(object):
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
        return self.line[self.pos]
