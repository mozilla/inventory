from django.db import models
from django.core.exceptions import ValidationError

from systems.models import System

import mozdns
from core.keyvalue.models import KeyValue
from core.mixins import ObjectUrlMixin
from mozdns.address_record.models import BaseAddressRecord
from mozdns.models import MozdnsRecord
from mozdns.domain.models import Domain
from mozdns.ip.models import Ip
from settings import CORE_BASE_URL

import re
import pdb

class StaticInterface(BaseAddressRecord, models.Model, ObjectUrlMixin):
    """The StaticInterface Class.

        >>> a = AddressRecord(label=label, domain=domain, ip_str=ip_str,
        ... ip_type=ip_type)
        >>> a.save()
        >>> ptr = PTR(ip_str=ip_str, ip_type=ip_type, name=a.fqdn)
        >>> ptr.save()
        >>> StaticInterface(address_record=a, ptr=ptr, mac=mac_address)

    This class is the main interface to DNS and DHCP in mozdns. A static
    interface consists of three key pieces of information: Ip address, Mac
    Address, and Hostname (the hostname is comprised of a label and a domain).
    From these three peices of information, three things are ensured: An A or
    AAAA DNS record, a PTR record, and a `host` statement in the DHCP builds
    that grants the mac address of the interface the correct IP address and
    hostname.

    If you want an A/AAAA, PTR, and a DHCP lease, create on of these objects.

    In terms of DNS, a static interface represents a PTR and A record and must
    adhear to the requirements of those classes. The interface inherits from
    AddressRecord and will call it's clean method with 'update_reverse_domain'
    set to True. This will ensure that it's A record is valid *and* that it's
    PTR record is valid.
    """
    id = models.AutoField(primary_key=True)
    reverse_domain = models.ForeignKey(Domain, null=True, blank=True,
            related_name='staticintrdomain_set')

    system = models.ForeignKey(System, null=True, blank=True)

    def details(self):
        return (
                ('Name', self.fqdn),
                ('DNS Type', 'A/PTR'),
                ('IP', self.ip_str),
                )
    class Meta:
        db_table = 'static_interface'
        unique_together = ('ip_upper', 'ip_lower', 'label', 'domain')

    def get_edit_url(self):
        return "/core/interface/{0}/{1}/update/".format(self.system.pk,
                self.pk)

    def get_absolute_url(self):
        return "/systems/show/{0}/".format(self.system.pk)

    def clean(self):
        #if not isinstance(self.mac, basestring):
        #    raise ValidationError("Mac Address not of valid type.")
        #self.mac = self.mac.lower()
        from mozdns.ptr.models import PTR
        if PTR.objects.filter(ip_str=self.ip_str, name=self.fqdn).exists():
            raise ValidationError("A PTR already uses this Name and IP")
        from mozdns.address_record.models import AddressRecord
        if AddressRecord.objects.filter(ip_str=self.ip_str, fqdn=self.fqdn
                ).exists():
            raise ValidationError("An A record already uses this Name and IP")

        """
        TODO, Huge Bug. Glue records are, at this point, only tied to address
        records. Interfaces can't be glue records. If this is going to be
        fixed. A lot of tests need to be written.
        """
        super(StaticInterface, self).clean(validate_glue=False,
                update_reverse_domain=True, ignore_interface=True)

    def delete(self):
        super(StaticInterface, self).delete(validate_glue=False)

    def get_absolute_url(self):
        """
        Return the absolute url of an object.
        """
        return CORE_BASE_URL + "/{0}/interface/{1}/".format(
            'systems', self.system.pk
        )

    def __repr__(self):
        return "<StaticInterface: {0}>".format(str(self))
    def __str__(self):
        #return "IP:{0} Full Name:{1} Mac:{2}".format(self.ip_str,
        #        self.fqdn, self.mac)
        return "IP:{0} Full Name:{1}".format(self.ip_str,
                self.fqdn)


is_eth = re.compile("^eth\d+$")
is_mgmt = re.compile("^mgmt\d+$")
class StaticIntrKeyValue(KeyValue):
    intr = models.ForeignKey(StaticInterface, null=False)
    class Meta:
        db_table = 'static_inter_key_value'
        unique_together = ('key', 'value')

    def name(self):
        if is_eth.match(self.value) or is_mgmt.match(self.value):
            return
        else:
            raise ValidationError("Name must be eth[0..] or mgmt[0..]")
