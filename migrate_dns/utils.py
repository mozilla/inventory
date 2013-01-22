INV_URL = "https://inventory.mozilla.org/en-US/"
import pdb
import re

INFO = 0
WARNING = 1
ERROR = 2
DEBUG = 3
BUILD = 4

def log(msg, level=0):
    """
    0 - Info
    1 - Warning
    2 - Error
    3 - Debug
    4 - Build
    """
    do_info = True
    do_warning = True
    do_error = True
    do_debug = True
    do_build = True
    if do_info and level == 0:
        print "[INFO] {0}\n".format(msg),
        return
    elif do_warning and level == 1:
        print "[WARNING] {0}\n".format(msg),
        return
    elif do_error and level == 2:
        print "[ERROR] {0}\n".format(msg),
        return
    elif do_debug and level == 3:
        print "[DEBUG] {0}\n".format(msg),
        return
    elif do_build and level == 4:
        print "[BUILD] {0}".format(msg),
        return

def print_system(system):
    return "{0} ({1}systems/edit/{2}/)".format(system, INV_URL, system.pk)

"""
>>> ip_to_domain_name('10.20.30.40')
'40.30.20.10.IN-ADDR.ARPA'
>>> ip_to_domain_name('10.20.30.40', lowercase=True)
'40.30.20.10.in-addr.arpa'
"""
def _ip_to_domain_name(ip, lowercase=False):
    """Convert an ip to dns zone form. The ip is assumed to be in valid dotted
    decimal format."""
    octets = ip.split('.')
    name = '.IN-ADDR.ARPA.'
    if lowercase:
        name = name.lowercase

    name = '.'.join(list(reversed(octets))) + name
    return name

def dns2ip_form(dnsip):
    dnsip = dnsip.upper()
    dnsip = dnsip.replace('.IN-ADDR.ARPA.', '')
    return '.'.join(list(reversed(dnsip.split('.'))))

def ensure_include(file_, file_type, include_file):
    """This function is magical. It will make sure that the 'include_file' has
    an $INCLUDE statement that includes it. See :function:`_ensure_include` for
    more info.

    :param include_file: the file to be included
    :type include_file: str
    :param file_type: The type of DNS zone file. Either 'forward' or 'reverse'
    :type file_type: str
    :param file_: The file with the SOA in it.
    :type file_: file
    """
    fd = open(file_, 'r+')
    try:
        new_content = _ensure_include(fd, file_type, include_file)
        fd.close()
        fd = open(file_, 'w+')
        fd.write(new_content)
    except Exception, e:
        raise Exception
    finally:
        fd.close()

def _ensure_include(text, file_type, include_file):
    """Read in a zone file and ensure that the string::

        $INCLUDE <include_file>

    exists somewhere in the file. If it does exist return None. If it doesn't
    exist insert the statment above the _first_ A/PTR record found in the file.

    :param text: the zone file.
    :type text: A file-ish object (StringIO or actual file)
    :param file_type: The type of DNS zone file. Either 'forward' or 'reverse'
    :type file_type: str
    :param include_file: the file to be included
    :type include_file: str
    """
    if _has_include(text, include_file):
        text.seek(0)
        return text.read()

    text.seek(0)  # Reset fp
    done = False
    return_text = ""
    comment = "This include preserves $ORIGIN"

    if file_type == 'forward':
        matches = [re.compile("^\s*\S*\s*IN\s*A\s*.*"),
            re.compile("^\s*\S*\s*IN\s*AAAA\s*.*")]  # Match A and AAAA
    else:
        # Must be 'reverse'
        matches = [re.compile("^\s*\S*\s*IN\s*PTR\s*.*")]  # Match PTR

    for raw_line in text.readlines():
        if done == True:
            return_text += raw_line
            continue

        line = raw_line.strip()
        for regex in matches:
            if regex.match(line):
                log("Inventory include not found. Adding $INCLUDE "
                        "{0}".format(include_file), INFO)
                return_text += "\n"
                return_text += "$INCLUDE {0} ; {1}\n".format(include_file, comment)
                return_text += "\n"
                done = True

        return_text += raw_line

    return return_text

def _has_include(text, include_file=None):
    """Sanity check."""

    is_file_include = re.compile("^\s*\$INCLUDE\s*([^;\s]*)\s*")

    done = False
    for raw_line in text.readlines():
        file_include = is_file_include.match(raw_line)
        if file_include:
            include_str = file_include.groups(0)[0]
            include_str = include_str.strip("'").strip('"')
            if include_str == include_file:
                log("Found existing include str: {0}".format(include_str), DEBUG)
                return True

    return False


def get_serial(file_):
    """
    Retrieve the serial number of a zone.

    :param file_: The file with the SOA in it.
    :type file_: file
    """
    with open(file_, 'r') as fd:
        return _str_get_soa(fd)

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
                return None

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
            return None

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
