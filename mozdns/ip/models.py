from django.db import models
from django.core.exceptions import ValidationError

from mozdns.domain.models import Domain, name_to_domain
from mozdns.validation import validate_ip_type
from mozdns.ip.utils import ip_to_domain_name, nibbilize

import ipaddr

import pdb


class Ip(models.Model):
    """An :class:`Ip` instance represents either an IPv4 or IPv6 address.

    :class:`Ip` instances are used in the :ref:`address_record` (A and AAAA
    records), :ref:`ptr`, and the :ref:`staticinterface` classes.

    :class:`Ip` instances in a :ref:`ptr` record must be mapped back to a
    Reverse :ref:`domain` object. A :class:`ValidationError` is raised if an
    eligible Reverse :ref:`domain` cannot be found when trying to create the
    :ref:`ptr`'s :class:`Ip`.

    The reason why an IP must be mapped back to a Reverse :ref:`domain` has to
    do with how bind files are generated. In a reverse zone file, ip addresses
    are mapped from IP to DATA. For instance an :ref:`ptr` record would
    look like this::

        IP                  DATA
        197.1.1.1   PTR     foo.bob.com

    If we were building the file ``197.in-addr.arpa``, all IP addresses
    in the ``197`` domain would need to be in this file. To reduce the
    complexity of finding records for a reverse domain, an :class:`IP` is
    linked to it's appropriate reverse domain when it is created. It's
    mapping is updated when it's reverse domain is deleted or a more
    appropritate reverse domain is added.  Keeping the :class:`Ip` feild on
    :ref:`ptr` will help preformance when building reverse zone files.

    The algorithm for determineing which reverse domain an :class:`Ip`
    belongs to is done by applying a 'longest prefix match' to all
    reverse domains in the :ref:`domain` table.

    :ref:`address_record` objects need the ip validation that happens in this class
    but do not need their :class:`Ip`'s to be tied back to a reverse domain.

    :ref:`staticinterface` objects need to have their ip tied back to reverse
    domain because they represent a :ref:`PTR` record as well as an
    :ref:`address_record`.

    .. note::
        Django's BigInteger wasn't "Big" enough, so there is code
        in `mozdns/ip/sql/ip.sql` that Alters the IP table.

    .. note::
        This class is abstract.

    """
    IP_TYPE_CHOICES = (('4', 'ipv4'), ('6', 'ipv6'))
    ip_str = models.CharField(max_length=39, editable=True, help_text='IP Address in IPv4 or IPv6 Format')
    # ip_upper/lower are calculated from ip_str on ip_clean.
    # TODO rename ip_* to ipaddr_*
    ip_upper = models.BigIntegerField(null=True, blank=True)
    ip_lower = models.BigIntegerField(null=True, blank=True)
    # TODO, should reverse_domain go into the PTR model?  I would think
    # it shouldn't because it is used in this class during the ip_clean
    # function.  Technically the ip_clean function would work if the
    # field existed in the PTR model, but overall it would hurt
    # readability.
    #
    # reactor.addCallback(think_about_it)
    # This can't be factored out because the related name classes. i.e.:
    # address_record.addressrecord: Accessor for field 'domain' clashes with
    # related field 'Domain.addressrecord_set'. Add a related_name argument to
    # the definition for 'domain'.
    #reverse_domain = models.ForeignKey(Domain, null=True, blank=True)
    ip_type = models.CharField(max_length=1, choices=IP_TYPE_CHOICES,
                               editable=True, help_text='IPv4 or IPv6 Address type')

    class Meta:
        abstract = True

    def clean_ip(self, update_reverse_domain=True):
        """The clean method in Ip is different from the rest. It needs
        to be called with the update_reverse_domain flag. Sometimes we
        need to not update the reverse domain of an IP (i.e. when we are
        deleting a reverse_domain).
        """
        # TODO, it's a fucking hack. Car babies.
        validate_ip_type(self.ip_type)
        self._validate_ip_str()
        if self.ip_type == '4':
            try:
                ip = ipaddr.IPv4Address(self.ip_str)
                self.ip_str = str(ip)
            except ipaddr.AddressValueError, e:
                raise ValidationError("Invalid Ip address {0}".
                                      format(self.ip_str))
            if update_reverse_domain:
                self.reverse_domain = name_to_domain(ip_to_domain_name(self.ip_str,
                    ip_type='4'))
                if (self.reverse_domain is None or self.reverse_domain.name in
                        ('arpa', 'in-addr.arpa', 'ipv6.arpa')):
                    raise ValidationError("No reverse Domain found for {0} "
                            .format(self.ip_str))
            self.ip_upper = 0
            self.ip_lower = int(ip)
        else:
            try:
                ip = ipaddr.IPv6Address(self.ip_str)
                self.ip_str = str(ip)
            except ipaddr.AddressValueError, e:
                raise ValidationError("Invalid ip {0} for IPv6s.".
                                      format(self.ip_str))

            if update_reverse_domain:
                nibz = nibbilize(self.ip_str)
                revname = ip_to_domain_name(nibz, ip_type='6')
                self.reverse_domain = name_to_domain(revname)
                if (self.reverse_domain is None or self.reverse_domain.name in
                        ('arpa', 'in-addr.arpa', 'ipv6.arpa')):
                    raise ValidationError("No reverse Domain found for {0} "
                            .format(self.ip_str))
            self.ip_upper, self.ip_lower = ipv6_to_longs(int(ip))

    def __int__(self):
        if self.ip_type == '4':
            self.ip_lower
        if self.ip_type == '6':
            return (self.ip_upper * (2 ** 64)) + self.ip_lower

    def _validate_ip_str(self):
        if isinstance(self.ip_str, basestring):
            return
        else:
            raise ValidationError("Plase provide the string representation"
                                  "of the IP")


def ipv6_to_longs(addr):
    """This function will turn an IPv6 into two longs. The first number
    represents the first 64 bits of the address and second represents
    the lower 64 bits.

    :param addr: IPv6 to be converted.
    :type addr: str
    :returns: (ip_upper, ip_lower) -- (int, int)
    :raises: ValidationError
    """
    try:
        ip = ipaddr.IPv6Address(addr)
    except ipaddr.AddressValueError, e:
        raise ValidationError("AddressValueError: Invalid IPv6 address {0}".
                              format(addr))
    # TODO, use int() instead of _int. Make sure tests pass
    ip_upper = ip._ip >> 64  # Put the last 64 bits in the first 64
    ip_lower = ip._ip & (1 << 64) - 1  # Mask off the last sixty-four bits
    return (ip_upper, ip_lower)
