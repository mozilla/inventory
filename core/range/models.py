from django.db import models
from django.core.exceptions import ValidationError

from core.network.models import Network
from core.mixins import ObjectUrlMixin
from core.keyvalue.models import KeyValue

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
    start = models.PositiveIntegerField(null=True)
    start_str = models.CharField(max_length=39, editable=True)
    end = models.PositiveIntegerField(null=True)
    end_str = models.CharField(max_length=39, editable=True)

    network = models.ForeignKey(Network, null=False)

    class Meta:
        db_table = 'range'
        unique_together = ('start', 'end')

    def save(self, *args, **kwargs):
        self.clean()
        super(Range, self).save(*args, **kwargs)

    def clean(self):
        if not self.network:
            raise ValidationError("ERROR: No network found")
        try:
            if self.network.ip_type == '4':
                self.start = int(ipaddr.IPv4Address(self.start_str))
                self.end = int(ipaddr.IPv4Address(self.end_str))
            elif self.network.ip_type == '6':
                raise NotImplemented
            else:
                raise ValidationError("ERROR: could not determine the ip type")
        except ipaddr.AddressValueError, e:
            raise ValidationError(str(e))

        if self.start >= self.end:
            raise ValidationError("The start of a range cannot be greater than"
                    " or equal to the end of the range.")

        self.network.update_network()
        if self.start < int(self.network.network.network):
        #lol, network.network.network.network.network....
            raise ValidationError("The start of a range cannot be less than "
                "it's network's network address.")
        if self.end > int(self.network.network.broadcast):
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
            if self.start > range_.end:
                continue
            if self.end < range_.start:
                continue
            raise ValidationError("Ranges cannot exist inside of other "
                "ranges.")

    def __str__(self):
        return "Site: {0} Vlan: {1} Network: {2} Range: Start - {3} End - {4}".format(
                #'self.network.site', 'self.network.vlan', self.network,
                self.network.site, self.network.vlan, self.network,
                self.start_str, self.end_str)

    def display(self):
        return "Range: {3} to {4}  {0} -- {2} -- {1}  ".format(
                #'self.network.site', 'self.network.vlan', self.network,
                self.network.site, self.network.vlan, self.network,
                self.start_str, self.end_str)

    def __repr__(self):
        return "<Range: {0}>".format(str(self))

class RangeKeyValue(KeyValue):
    range = models.ForeignKey(Range, null=False)
    aux_attrs = (
        ('type', 'The type of range.'),
    )
    class Meta:
        db_table = 'range_key_value'
        unique_together = ('key', 'value')

    def type(self):
        return
