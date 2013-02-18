from django.db import models
from django.core.exceptions import ValidationError

from systems.models import System

import mozdns
from core.keyvalue.models import KeyValue
from core.keyvalue.utils import AuxAttr
from core.validation import validate_mac
from mozdns.address_record.models import BaseAddressRecord
from mozdns.domain.models import Domain
from mozdns.ip.utils import ip_to_dns_form

import re
from gettext import gettext as _


class StaticInterface(BaseAddressRecord):
    """The StaticInterface Class.

        >>> s = StaticInterface(label=label, domain=domain, ip_str=ip_str,
        ... ip_type=ip_type, dhcp_enabled=True, dns_enabled=True)
        >>> s.full_clean()
        >>> s.save()

    This class is the main interface to DNS and DHCP in mozinv. A static
    interface consists of three key pieces of information: Ip address, Mac
    Address, and Hostname (the hostname is comprised of a label and a domain).
    From these three peices of information, three things are ensured: An A or
    AAAA DNS record, a PTR record, and a `host` statement in the DHCP builds
    that grants the mac address of the interface the correct IP address and
    hostname.

    If you want an A/AAAA, PTR, and a DHCP lease, create on of these objects.

    In terms of DNS, a static interface represents a PTR and A record and must
    adhear to the requirements of those classes. The interface inherits from
    BaseAddressRecord and will call it's clean method with
    'update_reverse_domain' set to True. This will ensure that it's A record is
    valid *and* that it's PTR record is valid.


    Using the 'attrs' attribute.

    To interface with the Key Value store of an interface use the 'attrs'
    attribute. This attribute is a direct proxy to the Keys and Values in the
    Key Value store. When you assign an attribute of the 'attrs' attribute a
    value, a key is create/updated. For example:

    >>> intr = <Assume this is an existing StaticInterface instance>
    >>> intr.update_attrs()  # This updates the object with keys/values already
    >>> # in the KeyValue store.
    >>> intr.attrs.primary
    '0'

    In the previous line, there was a key called 'primary' and it's value
    would be returned when you accessed the attribute 'primary'.

    >>> intr.attrs.alias
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
    AttributeError: 'attrs' object has no attribute 'alias'

    Here 'attrs' didn't have an attribute 'alias' which means that there was no
    KeyValue with key 'alias'. If we wanted to create that key and give it a
    value of '0' we would do:

    >>> intr.attrs.alias = '0'

    This *immediately* creates a KeyValue pair with key='alias' and value='0'.

    >>> intr.attrs.alias = '1'

    This *immediately* updates the KeyValue object with a value of '1'. It is
    not like the Django ORM where you must call the `save()` function for any
    changes to propagate to the database.
    """
    id = models.AutoField(primary_key=True)
    mac = models.CharField(max_length=17, validators=[validate_mac],
                           help_text="Mac address in format XX:XX:XX:XX:XX:XX")
    reverse_domain = models.ForeignKey(Domain, null=True, blank=True,
                                       related_name="staticintrdomain_set")

    system = models.ForeignKey(System, null=True, blank=True,
                               help_text="System to associate the interface "
                               "with")
    dhcp_enabled = models.BooleanField(default=True,
                                       help_text="Enable dhcp for this "
                                       "interface?")
    dns_enabled = models.BooleanField(default=True,
                                      help_text="Enable dns for this "
                                      "interface?")

    attrs = None

    search_fields = ("mac", "ip_str", "fqdn")

    def update_attrs(self):
        self.attrs = AuxAttr(StaticIntrKeyValue, self)

    def details(self):
        return (
            ("Name", self.fqdn),
            ("DNS Type", "A/PTR"),
            ("IP", self.ip_str),
        )

    class Meta:
        db_table = "static_interface"
        unique_together = ("ip_upper", "ip_lower", "label", "domain", "mac")

    @classmethod
    def get_api_fields(cls):
        return super(StaticInterface, cls).get_api_fields() + [
            'mac', 'dhcp_enabled', 'dns_enabled']

    @property
    def rdtype(self):
        return 'INTR'

    def get_edit_url(self):
        return "/core/interface/{0}/update/".format(self.pk)

    def get_delete_url(self):
        return "/core/interface/{0}/delete/".format(self.pk)

    def get_absolute_url(self):
        return "/systems/show/{0}/".format(self.system.pk)

    def interface_name(self):
        self.update_attrs()
        try:
            itype, primary, alias = '', '', ''
            itype = self.attrs.interface_type
            primary = self.attrs.primary
            alias = self.attrs.alias
        except AttributeError:
            pass
        if itype == '' or primary == '':
            return "None"
        elif alias == '':
            return "{0}{1}".format(itype, primary)
        else:
            return "{0}{1}.{2}".format(itype, primary, alias)

    def clean(self, *args, **kwargs):
        self.mac = self.mac.lower()
        if not self.system:
            raise ValidationError("An interface means nothing without it's "
                                  "system.")
        from mozdns.ptr.models import PTR
        from mozdns.address_record.models import AddressRecord

        if PTR.objects.filter(ip_str=self.ip_str, name=self.fqdn).exists():
            raise ValidationError("A PTR already uses this Name and IP")
        if AddressRecord.objects.filter(ip_str=self.ip_str, fqdn=self.fqdn
                                        ).exists():
            raise ValidationError("An A record already uses this Name and IP")

        if kwargs.pop("validate_glue", True):
            self.check_glue_status()

        self.update_reverse_domain()
        self.check_no_ns_soa_condition(self.reverse_domain)
        super(StaticInterface, self).clean(validate_glue=False,
                                           ignore_interface=True)

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
            raise ValidationError(
                "This Interface represents a glue record "
                "for a Nameserver. Change the Nameserver to edit this "
                "record.")

    A_template = _("{bind_name:$rhs_just} {ttl} {rdclass:$rdclass_just}"
                   "{rdtype_clob:$rdtype_just} {ip_str:$lhs_just}")
    PTR_template = _("{dns_ip:$lhs_just} {ttl} {rdclass:$rdclass_just}"
                     " {rdtype_clob:$rdtype_just} {fqdn:1}.")

    def bind_render_record(self, pk=False, **kwargs):
        self.rdtype_clob = kwargs.pop('rdtype', 'INTR')
        if kwargs.pop('reverse', False):
            self.template = self.PTR_template
            self.dns_ip = ip_to_dns_form(self.ip_str)
        else:
            self.template = self.A_template
        return super(StaticInterface, self).bind_render_record(pk=pk, **kwargs)

    def record_type(self):
        return "A/PTR"

    def delete(self, *args, **kwargs):
        if kwargs.pop("validate_glue", True):
            if self.intrnameserver_set.exists():
                raise ValidationError(
                    "Cannot delete the record {0}. It is a "
                    "glue record.".format(self.record_type()))
        check_cname = kwargs.pop("check_cname", True)
        super(StaticInterface, self).delete(validate_glue=False,
                                            check_cname=check_cname)

    def __repr__(self):
        return "<StaticInterface: {0}>".format(str(self))

    def __str__(self):
        # return "IP:{0} Full Name:{1} Mac:{2}".format(self.ip_str,
        #        self.fqdn, self.mac)
        return "IP:{0} Full Name:{1}".format(self.ip_str,
                                             self.fqdn)


is_eth = re.compile("^eth$")
is_mgmt = re.compile("^mgmt$")


class StaticIntrKeyValue(KeyValue):
    obj = models.ForeignKey(
        StaticInterface, related_name='keyvalue_set', null=False
    )

    class Meta:
        db_table = "static_inter_key_value"
        unique_together = ("key", "value", "obj")

    def _aa_primary(self):
        """
        The primary number of this interface (I.E. eth1.0 would have a primary
        number of '1')
        """
        if not self.value.isdigit():
            raise ValidationError("The primary number must be a number.")

    def _aa_alias(self):
        """The alias of this interface (I.E. eth1.0 would have a primary
        number of '0')."""
        if not self.value.isdigit():
            raise ValidationError("The alias number must be a number.")

    def _aa_hostname(self):
        """DHCP option hostname
        """
        if not self.value:
            raise ValidationError("Hostname Required")

    def _aa_domain_name_servers(self):
        """DHCP option domain-name-servers
        """
        if not self.value:
            raise ValidationError("Domain Name Servers Required")

    def _aa_domain_name(self):
        """DHCP option domain-name
        """
        if not self.value:
            raise ValidationError("Domain Name Required")

    def _aa_filename(self):
        """DHCP option filename
        """
        if not self.value:
            raise ValidationError("Filename Required")

    def _aa_interface_type(self):
        """Either eth (ethernet) or mgmt (mgmt)."""
        if not (is_eth.match(self.value) or is_mgmt.match(self.value)):
            raise ValidationError("Interface type must either be 'eth' "
                                  "or 'mgmt'")
