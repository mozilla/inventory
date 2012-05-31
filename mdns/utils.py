INV_URL = "https://inventory.mozilla.org/en-US/"
import pdb
import re

def print_system(system):
    return "{0} ({1}/systems/edit/{2}/)".format(system, INV_URL, system.pk)

def inrement_soa(file_):
    """This function wil take a file with an SOA a in it, parse the file,
    incriment the SOA and write the new contents back to the file.

    :param file_: The file with the SOA in it.
    :type file_: file
    """
    fd = open(file_, 'w+')
    try:
        new_content = _str_increment_soa(fd)
        fd.write(new_content)
    except Exception, e:
        raise Exception
    finally:
        fd.close()

def _str_increment_soa(text):
    """Read in a zone file and incriment the SOA. Return the zone file with the
    inc'ed SOA as a string.

    :param text: the zone file.
    :type text: A file-ish object (StringIO or actual file)
    :returns new_text: this is the file with the serial inc'ed.
    """
    new_text = ''
    # We already know it's in valid format.
    isSOA = False
    done = False
    for raw_line in text.readlines():
        if done:
            new_text += raw_line
            continue

        line = raw_line.strip()
        ll = LexLine(line)
        if isSOA:
            # If we made it here, this should be the serial.
            serial = _lex_word(ll)
            assert(serial.isdigit() == True)
            new_text += raw_line.replace(serial, str(int(serial) + 1))
            done = True
            continue

        if not line or line[0] == '$' or line[0] == ';':
            # It's a directive
            new_text += raw_line
            continue

        # name        ttl class rr    name-server email-addr  (sn ref ret ex min)
        # 1           2   3     4     5           6            7  8   9   10 11
        # Everything up through 6 needs to be on the same line.
        state = 1
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
            new_text += raw_line
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
            new_text += raw_line
            # The serial must be on the next line
            continue

        assert(serial.isdigit() == True)
        new_text += raw_line.replace(serial, str(int(serial) + 1))
        done = True


    return new_text

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
