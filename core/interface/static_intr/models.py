from django.db import models
from django.core.exceptions import ValidationError

from systems.models import System

import mozdns
from core.keyvalue.models import KeyValue
from core.mixins import ObjectUrlMixin
from mozdns.address_record.models import BaseAddressRecord
from mozdns.models import MozdnsRecord
from mozdns.view.models import View
from mozdns.domain.models import Domain
from mozdns.cname.models import CNAME
from mozdns.ip.models import Ip
from settings import CORE_BASE_URL

import re
import pdb

class StaticInterface(BaseAddressRecord, models.Model, ObjectUrlMixin):
    """The StaticInterface Class.

        >>> s = StaticInterface(label=label, domain=domain, ip_str=ip_str,
        ... ip_type=ip_type)
        >>> s.full_clean()
        >>> s.save()

    This class is the main interface to DNS in mozdns. A static
    interface consists of three key pieces of information: Ip address
    Address, and Hostname (the hostname is comprised of a label and a domain).
    From these three peices of information, two things are ensured: An A or
    AAAA DNS record and a PTR record.


    In terms of DNS, a static interface represents a PTR and A record and must
    adhear to the requirements of those classes. The interface inherits from
    BaseAddressRecord and will call it's clean method with 'update_reverse_domain'
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
        return "/core/interface/{0}/update/".format(self.pk)
    def get_delete_url(self):
        return "/core/interface/{0}/delete/".format(self.pk)

    def get_absolute_url(self):
        return "/systems/show/{0}/".format(self.system.pk)

    def clean(self, *args, **kwargs):
        #if not isinstance(self.mac, basestring):
        #    raise ValidationError("Mac Address not of valid type.")
        #self.mac = self.mac.lower()
        if not self.system:
            raise ValidationError("An interface means nothing without it's "
                "system.")
        from mozdns.ptr.models import PTR
        if PTR.objects.filter(ip_str=self.ip_str, name=self.fqdn).exists():
            raise ValidationError("A PTR already uses this Name and IP")
        from mozdns.address_record.models import AddressRecord
        if AddressRecord.objects.filter(ip_str=self.ip_str, fqdn=self.fqdn
                ).exists():
            raise ValidationError("An A record already uses this Name and IP")

        if 'validate_glue' in kwargs:
            validate_glue = kwargs.pop('validate_glue')
        else:
            validate_glue = True

        if validate_glue:
            self.check_glue_status()

        super(StaticInterface, self).clean(validate_glue=False,
                update_reverse_domain=True, ignore_interface=True)

        if self.pk and self.ip_str.startswith('10.'):
            p = View.objects.filter(name='private')
            if p:
                self.views.add(p[0])
                super(StaticInterface, self).clean(validate_glue=False,
                        update_reverse_domain=True, ignore_interface=True)

    def check_glue_status(self):
        """If this interface is a 'glue' record for a Nameserver instance,
        do not allow modifications to this record. The Nameserver will
        need to point to a different record before this record can
        be updated.
        """
        if self.pk is None:
            return
        # First get this object from the database and compare it to the
        # Nameserver object about to be saved.
        db_self = StaticInterface.objects.get(pk=self.pk)
        if db_self.label == self.label and db_self.domain == self.domain:
            return
        # The label of the domain changed. Make sure it's not a glue record
        Nameserver = mozdns.nameserver.models.Nameserver
        if Nameserver.objects.filter(intr_glue=self).exists():
            raise ValidationError("This Interface represents aa glue record "
                    "for a Nameserver. Change the Nameserver to edit this "
                    "record.")

    def delete(self, *args, **kwargs):
        if 'validate_glue' in kwargs:
            validate_glue = kwargs.pop('validate_glue')
        else:
            validate_glue = True
        if validate_glue:
            if self.intrnameserver_set.exists():
                raise ValidationError("Cannot delete the record {0}. It is a glue "
                    "record.".format(self.record_type()))
            if CNAME.objects.filter(data=self.fqdn):
                raise ValidationError("A CNAME points to this {0} record. Change "
                    "the CNAME before deleting this record.".
                    format(self.record_type()))
        super(StaticInterface, self).delete(validate_glue=False)

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

    def primary(self):
        if not self.value.isdigit():
            raise ValidationError("The primary number must be a number.")

    def alias(self):
        if not self.value.isdigit():
            raise ValidationError("The alias number must be a number.")
