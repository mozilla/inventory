from django.db import models
from django.core.exceptions import ValidationError

from core.network.models import Network
from core.mixins import ObjectUrlMixin
from core.keyvalue.base_option import CommonOption
from core.interface.static_intr.models import StaticInterface
from mozdns.ip.models import ipv6_to_longs
from mozdns.address_record.models import AddressRecord

import ipaddr

import pdb


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
    ---------------
    Things that happen when a static range is changed:
        * The new `start` and `end` values are checked against the range's
         network to ensure that the range still exists within the network.
        * The new `start` and `end` values are checked against all other
         existing range's `start` and `end` values to make sure that the new
         range does not overlap.
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

    class Meta:
        db_table = 'range'
        unique_together = ('start_upper', 'start_lower', 'end_upper', 'end_lower')

    def save(self, *args, **kwargs):
        self.clean()
        super(Range, self).save(*args, **kwargs)

    def clean(self):
        if not self.network:
            raise ValidationError("ERROR: No network found")
        try:
            if self.network.ip_type == '4':
                self.start_upper, self.start_lower = 0 ,int(
                        ipaddr.IPv4Address(self.start_str))
                self.end_upper, self.end_lower = 0 ,int(
                        ipaddr.IPv4Address(self.end_str))
            elif self.network.ip_type == '6':
                self.start_upper, self.start_lower = ipv6_to_longs(
                        self.start_str)
                self.end_upper, self.end_lower = ipv6_to_longs(
                        self.end_str)
            else:
                raise ValidationError("ERROR: could not determine the ip type")
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
        fail = False
        if self.start_upper > self.end_upper:
            # start > end
            fail = True
        if (self.start_upper == self.end_upper and self.start_lower >
            self.end_lower):
            # start > end
            fail = True
        if (self.start_upper == self.end_upper and self.start_lower ==
            self.end_lower):
            # end == start
            fail = True

        if fail:
            raise ValidationError("The start of a range cannot be greater than"
                    " or equal to the end of the range.")

        self.network.update_network()
        if self.network.ip_type == '4':
            IPClass = ipaddr.IPv4Address
        else:
            IPClass = ipaddr.IPv6Address

        if IPClass(self.start_str) < self.network.network.network:
            #lol, network.network.network.network.network....
            raise ValidationError("The start of a range cannot be less than "
                "it's network's network address.")
        if IPClass(self.end_str) > self.network.network.broadcast:
            raise ValidationError("The end of a range cannot be more than "
                "it's network's broadcast address.")

        self.check_for_overlaps()

    def check_for_overlaps(self):
        """This function will look at all the other ranges and make sure we
        don't overlap with any of them.
        """
        for range_ in self.network.range_set.all():
            if range_.pk == self.pk:
                continue

            # start > end
            if self.start_upper > range_.end_upper:
                continue
            if (self.start_upper == range_.end_upper and self.start_lower >
                range_.end_lower):
                continue
            # end < start
            if self.end_upper < range_.start_upper:
                continue
            if (self.end_upper == range_.start_upper and self.end_lower <
                range_.start_lower):
                continue
            raise ValidationError("Ranges cannot exist inside of other "
                "ranges.")

    def __str__(self):
        x = "Site: {0} Vlan: {1} Network: {2} Range: Start - {3} End -  {4}"
        return x.format(self.network.site, self.network.vlan, self.network,
            self.start_str, self.end_str)

    def display(self):
        return "Range: {3} to {4}  {0} -- {2} -- {1}  ".format(
                #'self.network.site', 'self.network.vlan', self.network,
                self.network.site, self.network.vlan, self.network,
                self.start_str, self.end_str)

    def __repr__(self):
        return "<Range: {0}>".format(str(self))

    def get_next_ip(self):
        """Find's the most appropriate ip address within a range. If it can't
        find an IP it returns None. If it finds an IP it returns an IPv4Address
        object.
            :returns: ipaddr.IPv4Address
        """
        if self.network.ip_type != '4':
            return None
        start = self.start_lower
        end = self.end_lower
        if start >= end - 1:
            return HttpResponse("Too small of a range.")

        records = AddressRecord.objects.filter(ip_upper=0, ip_lower__gte=start,
                ip_lower__lte=end)
        intrs = StaticInterface.objects.filter(ip_upper=0, ip_lower__gte=start,
                ip_lower__lte=end)
        if not records and not intrs:
            ip = ipaddr.IPv4Address(start)
            return ip
        for i in range(start, end + 1):
            taken = False
            for record in records:
                if record.ip_lower == i:
                    taken = True
                    break
            if taken == False:
                for intr in intrs:
                    if intr.ip_lower == i:
                        taken = True
                        break
            if taken == False:
                ip = ipaddr.IPv4Address(i)
                return ip
        return None


class RangeKeyValue(CommonOption):
    range = models.ForeignKey(Range, null=False)

    class Meta:
        db_table = 'range_key_value'
        unique_together = ('key', 'value', 'range')

    def _aa_failover(self):
        self.is_statement = True
        self.is_option = False
        if self.value != "peer \"dhcp-failover\"":
            raise ValidationError("Invalid failover option. Try `peer "
                "\"dhcp-failover\"`")

    def _aa_routers(self):
        self._routers(self.range.network.ip_type)

    def _aa_ntp_servers(self):
        self._ntp_servers(self.range.network.ip_type)
