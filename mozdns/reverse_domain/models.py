from django.db import models
from django.forms import ValidationError

from mozdns.soa.models import SOA
from mozdns.validation import validate_reverse_name
from mozdns.mixins import ObjectUrlMixin
from mozdns.validation import validate_ip_type, do_zone_validation

import ipaddr
import pdb


class ReverseDomain(models.Model, ObjectUrlMixin):
    """
    A reverse DNS domain is used to build reverse bind files. Every
    ``Ip`` object is mapped back to a ``ReverseDomain`` object.

    A ``ValidationError`` is raised when you are trying to add an Ip to
    the database.mozdns and it cannot be paired with a reverse domain. The
    solution is to create a reverse domain for the Ip to live in.

    A ``ValidationError`` is raised when you try to delete a reverse
    domain that has child reverse domains. A reverse domain should only
    be deleted when it has no child reverse domains.

    All reverse domains should have a master (or parent) reverse domain.
    A ``ValidationError`` will be raised if you try to create a reverse
    domain that should have a master reverse domain.

    The ``ip_type`` must be either '4' or '6'. Any other values will
    cause a ``ValidationError`` to be raised when calling an objects
    ``full_clean`` method.

    If you are not authoritative for a reverse domain, set the ``soa``
    field to ``None``.

    The ``name`` field must be unique. Failing to make it unique will
    raise a ``ValidationError``.

    >>> ReverseDomain(name=name)

    """
    IP_TYPE_CHOICES = (('4', 'IPv4'), ('6', 'IPv6'))
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True, null=False,
                            blank=False)

    master_reverse_domain = models.ForeignKey("self", null=True, blank=True)
    soa = models.ForeignKey(SOA, null=True, blank=True)
    ip_type = models.CharField(max_length=1, choices=IP_TYPE_CHOICES,
                               default='4', validators=[validate_ip_type])

    delegated = models.BooleanField(default=False, null=False, blank=True)
    # 'dirty' indicates if this reverse domain (and zone) needs to be rebuilt
    dirty = models.BooleanField(default=False)


    def __init__(self, *args, **kwargs):
        super(ReverseDomain, self).__init__(*args, **kwargs)

    class Meta:
        db_table = 'reverse_domain'

    def details(self):
        return (
            ('Name', self.name),
            ('Master Reverse Domain', self.master_reverse_domain),
            ('SOA', self.soa),
            ('Delegated', self.delegated),
        )

    def delete(self, *args, **kwargs):
        self._check_for_children()
        # Reassign Ip's in my reverse domain to my parent's reverse domain.
        self._reassign_reverse_ips_delete()
        super(ReverseDomain, self).delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.full_clean()
        super(ReverseDomain, self).save(*args, **kwargs)
        # Collect any ip's that belong to me.
        _reassign_reverse_ips(self, self.master_reverse_domain, self.ip_type)

    def clean(self):
        validate_reverse_name(self.name, self.ip_type)
        self.name = self.name.lower()
        self.master_reverse_domain = _name_to_master_reverse_domain(self.name,
                                                        ip_type=self.ip_type)
        do_zone_validation(self)

    def __str__(self):
        return "{0}".format(self.name)

    def __repr__(self):
        return "<ReverseDomain {0}>".format(str(self))

    def _reassign_reverse_ips_delete(self):
        """
        This function serves as a pretty subtle workaround.

            * An Ip is not allowed to have a reverse_domain of None.

            * When you save an Ip it is automatically assigned the most
              appropriate reverse_domain

        Passing the update_reverse_domain as False will by pass the Ip's
        class attempt to find an appropriate reverse_domain. This way
        you can reassign the reverse_domain of an Ip, save it, and then
        delete the old reverse_domain.
        """
        # TODO is there a better way of doing this?
        ptrs = self.ptr_set.iterator()
        for ptr in ptrs:
            ptr.reverse_domain = self.master_reverse_domain
            ptr.save()

    def _check_for_children(self):
        # TODO, merge forward and reverse "_check_for_children"
        children = ReverseDomain.objects.filter(master_reverse_domain=self)
        if children:
            error = ""
            for child in children:
                error = error.join(str(child) + ", ")
            raise ValidationError("Domain {0} has children {1}".
                                  format(self.name, error[:-2]))


# Handy Reverse Domain functions

def ip_to_reverse_domain(ip, ip_type):
    """Given an ip return the most specific reverse domain that the ip
    can belong to.

    :param ip: The ip to which we are using to search for a reverse
        domain.
    :type ip: str

    :param ip_type: The type of Ip address. It should be either an IPv4
        or IPv6 address.
    :type ip_type: str -- '4' or '6'

    :returns: reverse_domain -- :class:`ReverseDomain` object

    :raises: ValidationError
    """
    if ip_type == '6':
        ip = nibblize(ip)
    tokens = ip.split('.')
    reverse_domain = None
    for i in reversed(range(1,len(tokens))):
        search_reverse_domain = '.'.join(tokens[:-i])
        tmp_reverse_domain = ReverseDomain.objects.filter(
                                name = search_reverse_domain,
                                ip_type=ip_type)
        if tmp_reverse_domain:
            reverse_domain = tmp_reverse_domain[0]
        else:
            break # Since we have a full tree we must have reached a leaf node.
    if reverse_domain:
        return reverse_domain
    else:
        raise ValidationError("Error Could not find reverse domain for "
                              "ip '{0}'".format(ip))

def _name_to_master_reverse_domain(name, ip_type="4"):
    """Given an name return the most specific reverse_domain that the ip
    can belong to.

    note::
        A name x.y.z can be split up into x y and z. The
        reverse_domains, 'y.z' and 'z' should exist.

    :param name: The domain which we are using to search for a master
    reverse domain.

    :type name: str

    :param ip_type: The type of reverse domain. It should be either an
    IPv4 or IPv6 address.

    :type ip_type: str -- '4' or '6'

    :returns: ReverseDomain or None -- None if the reverse domain is a
    TLD

    :raises: ValidationError
    """
    tokens = name.split('.')
    master_reverse_domain = None
    for i in reversed(range(1,len(tokens))):
        parent_name = '.'.join(tokens[:-i])
        possible_master_reverse_domain = ReverseDomain.objects.filter(
                                            name = parent_name,
                                            ip_type=ip_type)

        if not possible_master_reverse_domain:
            raise ValidationError("Error: Coud not find master domain "
                                  "for {0}. Consider creating it.".
                                  format(name))
        else:
            master_reverse_domain = possible_master_reverse_domain[0]
    return master_reverse_domain


def _reassign_reverse_ips(reverse_domain_1, reverse_domain_2, ip_type):
    """There are some formalities that need to happen when a reverse
    domain is added and deleted. For example, when adding say we had the
    ip address 128.193.4.0 and it had the reverse_domain 128.193. If we
    add the reverse_domain 128.193.4, our 128.193.4.0 no longer belongs
    to the 128.193 domain. We need to re-asign the ip to it's correct
    reverse domain.

    :param reverse_domain_1: The domain which could possible have
    addresses added to it.

    :type reverse_domain_1: str

    :param reverse_domain_2: The domain that has ip's which might not
    belong to it anymore.

    :type reverse_domain_2: str
    """

    if reverse_domain_2 is None:
        return
    ptrs = reverse_domain_2.ptr_set.iterator()
    for ptr in ptrs:
        correct_reverse_domain = ip_to_reverse_domain(ptr.ip_str,
                                                      ip_type=ptr.ip_type)
        if correct_reverse_domain != ptr.reverse_domain:
            # TODO, is this needed? The save() function (actually the
            # clean_ip function) will assign the correct reverse domain.
            ptr.reverse_domain = correct_reverse_domain
            ptr.save()

def boot_strap_ipv6_reverse_domain(ip, soa=None):
    """
    This function is here to help create IPv6 reverse domains.

    .. note::
        Every nibble in the reverse domain should not exists for this
        function to exit successfully.


    :param ip: The ip address in nibble format
    :type ip: str
    :raises: ReverseDomainNotFoundError
    """
    validate_reverse_name(ip, '6')

    for i in range(1,len(ip)+1,2):
        cur_reverse_domain = ip[:i]
        reverse_domain = ReverseDomain(name = cur_reverse_domain, ip_type='6')
        reverse_domain.soa = soa
        reverse_domain.save()
    return reverse_domain


# TODO, should this go in ip.models?
"""
>>> nibblize('2620:0105:F000::1')
'2.6.2.0.0.1.0.5.F.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.1'
>>> nibblize('2620:0105:F000:9::1')
'2.6.2.0.0.1.0.5.f.0.0.0.0.0.0.9.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.1'
>>> nibblize('2620:0105:F000:9:0:1::1')
'2.6.2.0.0.1.0.5.f.0.0.0.0.0.0.9.0.0.0.0.0.0.0.1.0.0.0.0.0.0.0.1'
"""
def nibblize(addr):
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

    return '.'.join(list(ip_str.replace(':','')))
