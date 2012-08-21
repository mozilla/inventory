import ipaddr
from django.core.exceptions import ValidationError
from mozdns.validation import validate_ip_type

def ip_to_dns_form(ip, ip_type='4', uppercase=False):
    """Convert an ip to dns zone form. The ip is assumed to be in valid
    format."""
    if not isinstance(ip, basestring):
        raise ValidationError("Ip is not of type string.")
    validate_ip_type(ip_type)
    if ip_type == '4':
        octets = ip.split('.')
        name = '.in-addr.arpa'
    if ip_type == '6':
        octets = nibbilize(ip).split('.')
        name = '.ipv6.arpa'
    if uppercase:
        name = name.uppercase

    name = '.'.join(list(reversed(octets))) + name + "."
    return name

def ip_to_domain_name(ip, ip_type='4', uppercase=False):
    """Convert an ip to dns zone form. The ip is assumed to be in valid
    format."""
    if not isinstance(ip, basestring):
        raise ValidationError("Ip is not of type string.")
    validate_ip_type(ip_type)
    octets = ip.split('.')
    if ip_type == '4':
        name = '.in-addr.arpa'
    if ip_type == '6':
        name = '.ipv6.arpa'
    if uppercase:
        name = name.uppercase

    name = '.'.join(list(reversed(octets))) + name
    return name



"""
>>> nibbilize('2620:0105:F000::1')
'2.6.2.0.0.1.0.5.F.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.1'
>>> nibbilize('2620:0105:F000:9::1')
'2.6.2.0.0.1.0.5.f.0.0.0.0.0.0.9.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.1'
>>> nibbilize('2620:0105:F000:9:0:1::1')
'2.6.2.0.0.1.0.5.f.0.0.0.0.0.0.9.0.0.0.0.0.0.0.1.0.0.0.0.0.0.0.1'
"""


def nibbilize(addr):
    """Given an IPv6 address is 'colon' format, return the address in
    'nibble' form::

        nibblize('2620:0105:F000::1')
        '2.6.2.0.0.1.0.5.F.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.1'

    :param addr: The ip address to convert
    :type addr: str
    """
    try:
        ip_str = ipaddr.IPv6Address(str(addr)).exploded
    except ipaddr.AddressValueError:
        raise ValidationError("Error: Invalid IPv6 address {0}.".format(addr))

    return '.'.join(list(ip_str.replace(':', '')))


def i64_to_i128(upper_int, lower_int):
    return upper_int << 64 + lower_int

def i128_to_i64(bigint):
    ip_upper = bigint >> 64
    ip_lower = bigint & (1 << 64) - 1
    return ip_upper, ip_lower
