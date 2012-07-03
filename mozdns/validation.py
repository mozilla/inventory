from django.core.exceptions import ValidationError

import string
import pdb


def do_zone_validation(domain):
    """Preform validation on domain. This function calls the following
    functions::

        check_for_soa_partition
        check_for_master_delegation
        validate_zone_soa

    .. note::
        The type of the domain that is passed is determined
        dynamically

    :param domain: The domain/reverse_domain being validated.
    :type domain: :class:`Domain` or :class:`ReverseDomain`

    The following code is an example of how to call this function during
    *domain* introspection.

        >>> do_zone_validation(self, self.master_domain)

    The following code is an example of how to call this function during
    *reverse_domain* introspection.

        >>> do_zone_validation(self, self.master_reverse_domain)

    """
    from mozdns.domain.models import Domain

    check_for_master_delegation(domain, domain.master_domain)
    validate_zone_soa(domain, domain.master_domain)
    check_for_soa_partition(domain, domain.domain_set.all())


def check_for_master_delegation(domain, master_domain):
    """No subdomains can be created under a domain that is delegated.
    This function checks whether a domain is violating that condition.

    :param domain: The domain/reverse_domain being validated.
    :type domain: :class:`Domain` or :class:`ReverseDomain`

    :param master_domain: The master domain/reverse_domain of the
        domain/reverse_domain being validated.
    :type master_domain: :class:`Domain` or :class:`ReverseDomain`

    The following code is an example of how to call this function during
    *domain* introspection.

        >>> check_for_master_delegation(self, self.master_domain)

    The following code is an example of how to call this function during
    *reverse_domain* introspection.

        >>> check_for_master_delegation(self, self.master_reverse_domain)

    """
    if not master_domain:
        return
    if not master_domain.delegated:
        return
    if not domain.pk:  # We don't exist yet.
        raise ValidationError("No subdomains can be created in the {0} "
                              "domain. It is delegated."
                                .format(master_domain.name))


def validate_zone_soa(domain, master_domain):
    """Make sure the SOA assigned to this domain is the correct SOA for
    this domain. Also make sure that the SOA is not used in a different
    zone.

    :param domain: The domain/reverse_domain being validated.
    :type domain: :class:`Domain` or :class:`ReverseDomain`

    :param master_domain: The master domain/reverse_domain of the
        domain/reverse_domain being validated.
    :type master_domain: :class:`Domain` or :class:`ReverseDomain`

    The following code is an example of how to call this function during
    *domain* introspection.

        >>> validate_zone_soa('forward', self, self.master_domain)

    The following code is an example of how to call this function during
    *reverse_domain* introspection.

        >>> validate_zone_soa('reverse', self, self.master_reverse_domain)

    """
    if not domain:
        raise Exception("You called this function wrong")

    if not domain.soa:
        return

    zone_domains = domain.soa.domain_set.all()
    root_domain = find_root_domain(domain.soa)

    if not root_domain:  # No one is using this domain.
        return

    if not zone_domains.exists():
        return  # No zone uses this soa.

    if master_domain and master_domain.soa != domain.soa:
        # Someone uses this soa, make sure the domain is part of that
        # zone (i.e. has a parent in the zone or is the root domain of
        # the zone).
        if root_domain == domain or root_domain.master_domain == domain:
            return
        raise ValidationError("This SOA is used for a different zone.")

    if domain.master_domain is None and domain != root_domain:
        if root_domain.master_domain == domain:
            return
        # If we are at the root of the tree and we aren't the root domain,
        # something is wrong.
        raise ValidationError("This SOA is used for a different zone.")


def check_for_soa_partition(domain, child_domains):
    """This function determines if changing your soa causes sub domains
    to become their own zones and if those zones share a common SOA (not
    allowed).

    :param domain: The domain/reverse_domain being validated.
    :type domain: :class:`Domain` or :class:`ReverseDomain`

    :param child_domains: A Queryset containing child objects of the
        :class:`Domain`/:class:`ReverseDomain` object.
    :type child_domains: :class:`Domain` or :class:`ReverseDomain`

    :raises: ValidationError

    The following code is an example of how to call this function during
    *domain* introspection.

        >>> check_for_soa_partition(self, self.domain_set.all())

    The following code is an example of how to call this function during
    *reverse_domain* introspection.

        >>> check_for_soa_partition(self, self.reversedomain_set.all())

    """
    for i_domain in child_domains:
        if i_domain.soa == domain.soa:
            continue  # Valid child.
        for j_domain in child_domains:
            # Make sure the child domain does not share an SOA with one
            # of it's siblings.
            if i_domain == j_domain:
                continue
            if i_domain.soa == j_domain.soa and i_domain.soa is not None:
                raise ValidationError("Changing the SOA for the {0} "
                        "domain would cause the child domains {1} and {2} to "
                        "become two zones that share the same SOA. Change "
                        "{3} or {4}'s SOA before changing this  SOA".
                        format(domain.name, i_domain.name, j_domain.name,
                            i_domain.name, j_domain.name))


def find_root_domain(soa):
    """
    It is nessicary to know which domain is at the top of a zone. This
    function returns that domain.

    :param soa: A zone's :class:`SOA` object.
    :type soa: :class:`SOA`

    The following code is an example of how to call this function using
    a Domain as ``domain``.

        >>> find_root_domain('forward', domain.soa)

    The following code is an example of how to call this function using
    a ReverseDomain as ``domain``.

        >>> find_root_domain('reverse', reverse_domain.soa)

    """

    if soa is None:
        return None

    domains = soa.domain_set.all()
    if domains:
        key = lambda domain: len(domain.name.split('.'))
        return sorted(domains, key=key)[0]  # Sort by number of labels
    else:
        return None

###################################################################
#        Functions that validate labels and names                 #
###################################################################
"""
MozAddressValueError
    This exception is thrown when an attempt is made to create/update a
    record with an invlaid IP.

InvalidRecordNameError
    This exception is thrown when an attempt is made to create/update a
    record with an invlaid name.

RecordExistsError
    This exception is thrown when an attempt is made to create a record
    that already exists.  All records that can support the
    unique_together constraint do so. These models will raise an
    IntegretyError. Some models, ones that have to span foreign keys to
    check for uniqueness, need to still raise ValidationError.
    RecordExistsError will be raised in these cases.

An AddressRecord is an example of a model that raises this Exception.
"""

def validate_first_label(label, valid_chars=None):
    """This function is just :fun:`validate_label` except it is called on just
    the first label. The first label *can* start with a '*' while a normal
    label cannot."""
    if label != '' and label[0] == '*':
        if len(label) == 1:
            return
        else:
            validate_label(label[1:])
    else:
        validate_label(label)

def validate_label(label, valid_chars=None):
    """Validate a label.

        :param label: The label to be tested.
        :type label: str

        "Allowable characters in a label for a host name are only ASCII
        letters, digits, and the '-' character."

        "Labels may not be all numbers, but may have a leading digit"

        "Labels must end and begin only with a letter or digit"

        -- `RFC <http://tools.ietf.org/html/rfc1912>`__

        "[T]he following characters are recommended for use in a host
        name: "A-Z", "a-z", "0-9", dash and underscore"

        -- `RFC <http://tools.ietf.org/html/rfc1033>`__

    """
    _name_type_check(label)

    if not valid_chars:
        # "Allowable characters in a label for a host name are only
        # ASCII letters, digits, and the `-' character." "[T]he
        # following characters are recommended for use in a host name:
        # "A-Z", "a-z", "0-9", dash and underscore"
        valid_chars = string.ascii_letters + "0123456789" + "-"

    # Labels may not be all numbers, but may have a leading digit TODO
    # Labels must end and begin only with a letter or digit TODO

    for char in label:
        if char == '.':
            raise ValidationError("Invalid name {0}. Please do not span "
                                  "multiple domains when creating records."
                                    .format(label))
        if valid_chars.find(char) < 0:
            raise ValidationError("Ivalid name {0}. Character '{1}' is "
                                  "invalid.".format(label, char))
    return


def validate_domain_name(name):
    """Domain names are different. They are allowed to have '_' in them.

        :param name: The domain name to be tested.
        :type name: str
    """
    _name_type_check(name)

    for label in name.split('.'):
        if not label:
            raise ValidationError("Error: Ivalid name {0}. Empty label."
                                    .format(label))
        valid_chars = string.ascii_letters + "0123456789" + "-_"
        validate_label(label, valid_chars=valid_chars)


def validate_name(fqdn):
    """Run test on a name to make sure that the new name is constructed
    with valid syntax.

        :param fqdn: The fqdn to be tested.
        :type fqdn: str


        "DNS domain names consist of "labels" separated by single dots."
        -- `RFC <http://tools.ietf.org/html/rfc1912>`__


        .. note::
            DNS name hostname grammar::

                <domain> ::= <subdomain> | " "

                <subdomain> ::= <label> | <subdomain> "." <label>

                <label> ::= <letter> [ [ <ldh-str> ] <let-dig> ]

                <ldh-str> ::= <let-dig-hyp> | <let-dig-hyp> <ldh-str>

                <let-dig-hyp> ::= <let-dig> | "-"

                <let-dig> ::= <letter> | <digit>

                <letter> ::= any one of the 52 alphabetic characters A
                through Z in upper case and a through z in lower case

                <digit> ::= any one of the ten digits 0 through 9

            --`RFC 1034 <http://www.ietf.org/rfc/rfc1034.txt>`__
    """
    # TODO, make sure the grammar is followed.
    _name_type_check(fqdn)

    # Star records are allowed. Remove them during validation.
    if fqdn[0] == '*':
        fqdn = fqdn[1:]
        fqdn = fqdn.strip('.')

    for label in fqdn.split('.'):
        if not label:
            raise ValidationError("Ivalid name {0}. Empty label."
                                    .format(label))
        validate_label(label)


def validate_reverse_name(reverse_name, ip_type):
    """Validate a reverse name to make sure that the name is constructed
    with valid syntax.

        :param reverse_name: The reverse name to be tested.
        :type reverse_name: str
    """
    _name_type_check(reverse_name)

    valid_ipv6 = "0123456789AaBbCcDdEeFf"

    if ip_type == '4' and len(reverse_name.split('.')) > 4:
        raise ValidationError("IPv4 reverse domains should be a "
                              "maximum of 4 octets")
    if ip_type == '6' and len(reverse_name.split('.')) > 32:
        raise ValidationError("IPv6 reverse domains should be a "
                              "maximum of 32 nibbles")

    for nibble in reverse_name.split('.'):
        if ip_type == '6':
            if valid_ipv6.find(nibble) < 0:
                raise ValidationError("Error: Ivalid Ipv6 name {0}. Character "
                                      "'{1}' is invalid."
                                        .format(reverse_name, nibble))
        else:
            if not(int(nibble) <= 255 and int(nibble) >= 0):
                raise ValidationError("Error: Ivalid Ipv4 name {0}. Character "
                                      "'{1}' is invalid."
                                        .format(reverse_name, nibble))

def validate_ttl(ttl):
    """
        "It is hereby specified that a TTL value is an unsigned number,
        with a minimum value of 0, and a maximum value of 2147483647."
        -- `RFC <http://www.ietf.org/rfc/rfc2181.txt>`__

        :param  ttl: The TTL to be validated.
        :type   ttl: int
        :raises: ValidationError
    """
    if ttl < 0 or ttl > 2147483647: # See RFC 2181
        raise ValidationError("TTLs must be within the 0 to "
                              "2147483647 range.")

# Works for labels too.
def _name_type_check(name):
    if type(name) not in (str, unicode):
        raise ValidationError("Error: A name must be of type str.")

###################################################################
#               Functions that Validate SRV fields                #
###################################################################

def validate_srv_port(port):
    """Port must be within the 0 to 65535 range."""
    if port > 65535 or port < 0:
        raise ValidationError("SRV port must be within 0 and 65535. "
                              "See RFC 1035")

#TODO, is this a duplicate of MX ttl?
def validate_srv_priority(priority):
    """Priority must be within the 0 to 65535 range."""
    if priority > 65535 or priority < 0:
        raise ValidationError("SRV priority must be within 0 and 65535. "
                              "See RFC 1035")

def validate_srv_weight(weight):
    """Weight must be within the 0 to 65535 range."""
    if weight > 65535 or weight < 0:
        raise ValidationError("SRV weight must be within 0 and 65535. "
                              "See RFC 1035")

def validate_srv_label(srv_label):
    """This function is the same as :func:`validate_label` expect
    :class:`SRV` records can have a ``_`` preceding its label.
    """
    if srv_label and srv_label[0] != '_':
        raise ValidationError("Error: SRV label must start with '_'")
    validate_label(srv_label[1:]) # Get rid of '_'

def validate_srv_name(srv_name):
    """This function is the same as :func:`validate_name` expect
    :class:`SRV` records can have a ``_`` preceding is name.
    """
    if srv_name and srv_name[0] != '_':
        raise ValidationError("Error: SRV label must start with '_'")
    if not srv_name:
        raise ValidationError("Error: SRV label must not be None")
    mod_srv_name = srv_name[1:] # Get rid of '_'
    validate_name(mod_srv_name)

###################################################################
#               Functions that Validate MX fields                 #
###################################################################

def validate_mx_priority(priority):
    """
    Priority must be within the 0 to 65535 range.
    """
    # This is pretty much the same as validate_srv_priority. It just has
    # a different error messege.
    if priority > 65535 or priority < 0:
        raise ValidationError("MX priority must be within the 0 to 65535 "
                              "range. See RFC 1035")

###################################################################
#               Functions Validate ip_type fields                 #
###################################################################

def validate_ip_type(ip_type):
    """
    An ``ip_type`` field must be either '4' or '6'.
    """
    if ip_type not in ('4', '6'):
        raise ValidationError("Error: Plase provide a valid ip type.")
