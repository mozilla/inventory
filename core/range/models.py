from django.db import models
from django.core.exceptions import ValidationError
from django.http import HttpResponse

from core.network.models import Network
from core.utils import IPFilter, four_to_two
from core.mixins import ObjectUrlMixin
from core.keyvalue.base_option import CommonOption, DHCPKeyValue
from core.registration.static.models import StaticReg
from mozdns.ip.models import ipv6_to_longs
from mozdns.address_record.models import AddressRecord
from mozdns.ptr.models import PTR

import ipaddr


class Range(models.Model, ObjectUrlMixin):
    """The Range class.

        >>> Range(start=start_ip, end=end_ip,
        >>>         defualt_domain=domain, network=network)


    Ranges live inside networks; their start ip address is greater than or
    equal to the the start of their network and their end ip address is less
    than or equal to the end of their network; both the Range and the network
    class enforce these requirements. Good practice says ranges should not
    start on the network address of their network and they should not end on
    the broadcast address of their network; the Range and Network classes do
    not enforce this.

    Chaning a Range

    Things that happen when a static range is changed:

        *   The new `start` and `end` values are checked against the range's
            network to ensure that the range still exists within the network.
        *   The new `start` and `end` values are checked against all other
            existing range's `start` and `end` values to make sure that the new
            range does not overlap.

    Ranges should try to enforce the host template found in Mana
    https://mana.mozilla.org/wiki/display/NETOPS/Node+deployment
    """
    id = models.AutoField(primary_key=True)

    start_upper = models.BigIntegerField(null=True)
    start_lower = models.BigIntegerField(null=True)
    start_str = models.CharField(max_length=39, editable=True)

    end_lower = models.BigIntegerField(null=True)
    end_upper = models.BigIntegerField(null=True)
    end_str = models.CharField(max_length=39, editable=True)

    dhcpd_raw_include = models.TextField(null=True, blank=True)

    network = models.ForeignKey(Network, null=False)
    is_reserved = models.BooleanField(default=False, blank=False)

    IP_TYPES = (
        ('4', 'IPv4'),
        ('6', 'IPv6'),
    )
    ip_type = models.CharField(
        max_length=1, choices=IP_TYPES, editable=False, null=True
    )

    STATIC = "st"
    DYNAMIC = "dy"
    RANGE_TYPE = (
        (STATIC, 'Static'),
        (DYNAMIC, 'Dynamic'),
    )
    rtype = models.CharField(
        max_length=2, choices=RANGE_TYPE, default=STATIC, editable=True
    )

    class Meta:
        db_table = 'range'
        unique_together = ('start_upper', 'start_lower', 'end_upper',
                           'end_lower')

    def __str__(self):
        return self.start_str + " <-> " + self.end_str

    def save(self, *args, **kwargs):
        self.clean()
        super(Range, self).save(*args, **kwargs)

    def clean(self):
        if not self.network:
            raise ValidationError("ERROR: No network found")
        try:
            if self.network.ip_type == '4':
                self.start_upper, self.start_lower = 0, int(
                    ipaddr.IPv4Address(self.start_str))
                self.end_upper, self.end_lower = 0, int(
                    ipaddr.IPv4Address(self.end_str))
            elif self.network.ip_type == '6':
                self.start_upper, self.start_lower = ipv6_to_longs(
                    self.start_str)
                self.end_upper, self.end_lower = ipv6_to_longs(self.end_str)
            else:
                raise ValidationError("ERROR: could not determine the ip type")
            self.ip_type = self.network.ip_type
        except ipaddr.AddressValueError, e:
            raise ValidationError(str(e))

        """
        Some notes:
        start = s1 s2
        end = e1 e2

        if s1 > e1:
            start > end
            # Bad
        if e1 > s1:
            end > start
            # Good
        if s1 == e1 and s2 > e2:
            start > end
            # Bad
        if s1 == e1 and s2 < e2:
            end > start
            # Good
        if s1 == e1 and s2 == e2:
            end == start
            # Bad
        """

        # Credit goes to fridgei
        start, end = four_to_two(
            self.start_upper, self.start_lower, self.end_upper, self.end_lower)
        if start > end:
            raise ValidationError(
                "The start of a range cannot be greater than or equal to the "
                "end of the range."
            )
        self.network.update_network()
        if self.network.ip_type == '4':
            IPClass = ipaddr.IPv4Address
        else:
            IPClass = ipaddr.IPv6Address

        if (IPClass(self.start_str) < self.network.network.network or
                IPClass(self.end_str) > self.network.network.broadcast):
            raise ValidationError(
                "Range {0}-{1} doesn't fit in {2}".format(
                    self.start_lower, self.end_lower, self.network.network
                )
            )
        self.check_for_overlaps()

    def _range_ips(self):
        # Credit goes to fridgei
        self._start, self._end = four_to_two(
            self.start_upper, self.start_lower, self.end_upper, self.end_lower
        )

    def check_for_overlaps(self):
        """
        This function will look at all the other ranges and make sure we
        don't overlap with any of them.
        """
        # Credit goes to fridgei
        self._range_ips()
        Ip = ipaddr.IPv4Address if self.ip_type == '4' else ipaddr.IPv6Address
        for range_ in Range.objects.all():
            if range_.pk == self.pk:
                continue
            range_._range_ips()
            #the range being tested is above this range
            if self._start > range_._end:
                continue
            # start > end
            if self._end < range_._start:
                continue
            raise ValidationError(
                "Stored range {0} - {1} would contain {2} - {3}".format(
                    Ip(range_._start), Ip(range_._end), Ip(self._start),
                    Ip(self._end)
                )
            )

    def desc(self):
        x = "Site: {0} Vlan: {1} Network: {2} Range: Start - {3} End -  {4}"
        return x.format(self.network.site, self.network.vlan, self.network,
                        self.start_str, self.end_str)

    def update_ipf(self):
        """Update the IP filter. Used for compiling search queries and firewall
        rules."""
        self.ipf = IPFilter(self.start_str, self.end_str, self.network.ip_type,
                            object_=self)

    def display(self):
        return "Range: {3} to {4}  {0} -- {2} -- {1}  ".format(
            self.network.site, self.network.vlan, self.network,
            self.start_str, self.end_str)

    def choice_display(self):
        if not self.network.site:
            site_name = "No Site"
        else:
            site_name = self.network.site.name.upper()

        if not self.network.vlan:
            vlan_name = "No Vlan"
        else:
            vlan_name = str(self.network.vlan)
        return "{0} - {1} - ({2}) {3} to {4}".format(
            site_name, vlan_name,
            self.network, self.start_str, self.end_str)

    def __repr__(self):
        return "<Range: {0}>".format(str(self))

    def get_next_ip(self):
        """
        Find's the most appropriate ip address within a range. If it can't
        find an IP it returns None. If it finds an IP it returns an IPv4Address
        object.

            :returns: ipaddr.IPv4Address
        """
        # TODO, use range_usage
        if self.network.ip_type != '4':
            return None
        start = self.start_lower
        end = self.end_lower
        if start >= end - 1:
            return HttpResponse("Too small of a range.")
        ip = find_free_ip(start, end, ip_type='4')
        if ip:
            return ip
        else:
            return None

    def range_usage(self):
        from core.range.utils import range_usage
        ru = range_usage(self.start_str, self.end_str, self.network.ip_type)
        ru_precent = ru['used'] / (ru['used'] + 0.0 + ru['unused'])
        ru['precent_used'] = str(ru_precent * 100)[0:4] + " %"
        return ru


def find_free_ip(start, end, ip_type='4'):
    """Given start and end numbers, find a free ip.
    :param start: The start number
    :type start: int
    :param end: The end number
    :type end: int
    :param ip_type: The type of IP you are looking for.
    :type ip_type: str either '4' or '6'
    """
    if ip_type == '4':
        records = AddressRecord.objects.filter(
            ip_upper=0, ip_lower__gte=start, ip_lower__lte=end
        )
        ptrs = PTR.objects.filter(
            ip_upper=0, ip_lower__gte=start, ip_lower__lte=end
        )
        sregs = StaticReg.objects.filter(
            ip_upper=0, ip_lower__gte=start, ip_lower__lte=end
        )
        if not records and not sregs:
            ip = ipaddr.IPv4Address(start)
            return ip
        for i in xrange(start, end + 1):
            taken = False
            for record in records:
                if record.ip_lower == i:
                    taken = True
                    break
            for ptr in ptrs:
                if ptr.ip_lower == i:
                    taken = True
                    break
            if not taken:
                for sreg in sregs:
                    if sreg.ip_lower == i:
                        taken = True
                        break
            if not taken:
                ip = ipaddr.IPv4Address(i)
                return ip
    else:
        raise NotImplemented()


class RangeKeyValue(DHCPKeyValue, CommonOption):
    obj = models.ForeignKey(Range, related_name='keyvalue_set', null=False)

    class Meta:
        db_table = 'range_key_value'
        unique_together = ('key', 'value', 'obj')

    def _aa_failover(self):
        self.is_statement = True
        self.is_option = False
        if self.value != "peer \"dhcp-failover\"":
            raise ValidationError("Invalid failover option. Try `peer "
                                  "\"dhcp-failover\"`")

    def _aa_routers(self):
        self._routers(self.obj.network.ip_type)

    def _aa_ntp_servers(self):
        self._ntp_servers(self.obj.network.ip_type)
