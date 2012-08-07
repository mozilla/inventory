from django.db import models
from django.core.exceptions import ValidationError, ObjectDoesNotExist

import mozdns
import core as core
from mozdns.cname.models import CNAME
from mozdns.view.models import View
from mozdns.ip.models import Ip
from mozdns.models import set_fqdn, check_for_cname, check_for_delegation
from mozdns.models import check_TLD_condition
from mozdns.validation import validate_first_label, validate_name
from mozdns.validation import validate_ttl, validate_views
from mozdns.domain.models import Domain
from mozdns.mixins import ObjectUrlMixin

import pdb


class BaseAddressRecord(Ip):
    """AddressRecord is the class that generates A and AAAA records

        >>> AddressRecord(label=label, domain=domain_object, ip_str=ip_str,
        ... ip_type=ip_type)

    """
    ############################
    # See Ip for all ip fields #
    ############################

    label = models.CharField(max_length=100, blank=True, null=True,
                             validators=[validate_first_label])
    domain = models.ForeignKey(Domain, null=False)
    fqdn = models.CharField(max_length=255, blank=True, null=True,
                            validators=[validate_name])
    views = models.ManyToManyField(View)
    ttl = models.PositiveIntegerField(default=3600, blank=True, null=True,
            validators=[validate_ttl])
    comment = models.CharField(max_length=1000, blank=True, null=True)

    search_fields = ('fqdn', 'ip_str')

    class Meta:
        abstract = True

    def details(self):
        return  (
                    ('FQDN', self.fqdn),
                    ('Record Type', self.record_type()),
                    ('IP', str(self.ip_str)),
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        set_fqdn(self)
        check_TLD_condition(self)
        self.domain.dirty = True
        self.domain.save()
        if self.pk:
            validate_views(self.views, self.ip_str, self.ip_type)
        super(BaseAddressRecord, self).save(*args, **kwargs)

    def clean(self, *args, **kwargs):
        validate_glue = kwargs.pop('validate_glue', True)
        if validate_glue:
            self.check_glue_status()
        set_fqdn(self)
        check_TLD_condition(self)
        if self.domain.delegated:
            self.validate_delegation_conditions()
        check_for_cname(self)


        urd = kwargs.pop('update_reverse_domain', False)
        self.clean_ip(update_reverse_domain=urd)

        if not kwargs.pop('ignore_interface', False):
            from core.interface.static_intr.models import StaticInterface
            if StaticInterface.objects.filter(fqdn=self.fqdn,
                    ip_upper=self.ip_upper, ip_lower=self.ip_lower).exists():
                raise ValidationError("A Static Interface has already "
                    "reserved this A record.")

    def delete(self, *args, **kwargs):
        """Address Records that are glue records or that are pointed to
        by a CNAME should not be removed from the database.
        """
        if kwargs.pop('validate_glue', True):
            if self.nameserver_set.exists():
                raise ValidationError("Cannot delete the record {0}. It is "
                    "a glue record.".format(self.record_type()))
        if kwargs.pop('check_cname', True):
            if CNAME.objects.filter(data=self.fqdn):
                raise ValidationError("A CNAME points to this {0} record. "
                    "Change the CNAME before deleting this record.".
                    format(self.record_type()))
        super(BaseAddressRecord, self).delete(*args, **kwargs)

    def set_fqdn(self):
        set_fqdn(self)

    def validate_delegation_conditions(self):
        """If our domain is delegated then an A record can only have a
        name that is the same as a nameserver in that domain (glue)."""
        if self.domain.nameserver_set.filter(server=self.fqdn).exists():
            return
        else:
            # Confusing error messege?
            raise ValidationError("You can only create A records in a "
                "delegated domain that have an NS record pointing to them.")

    def check_glue_status(self):
        """If this record is a 'glue' record for a Nameserver instance,
        do not allow modifications to this record. The Nameserver will
        need to point to a different record before this record can
        be updated.
        """
        if self.pk is None:
            return
        # First get this object from the database.mozdns and compare it to the
        # nameserver.nameserver.  object about to be saved.
        db_self = AddressRecord.objects.get(pk=self.pk)
        if db_self.label == self.label and db_self.domain == self.domain:
            return
        # The label of the domain changed. Make sure it's not a glue record
        Nameserver = mozdns.nameserver.models.Nameserver
        if Nameserver.objects.filter(addr_glue=self).exists():
            raise ValidationError("This record is a glue record for a"
                    "Nameserver. Change the Nameserver to edit this record.")

    def record_type(self):
        # If PTR didn't share this field, we would use 'A' and 'AAAA'
        # instead of '4' and '6'.
        if self.ip_type == '4':
            return 'A'
        else:
            return 'AAAA'

    def __str__(self):
        return "{0} {1} {2}".format(self.fqdn,
                                    self.record_type(), str(self.ip_str))

    def __repr__(self):
        return "<Address Record '{0}'>".format(str(self))


class AddressRecord(BaseAddressRecord, ObjectUrlMixin):
    """AddressRecord is the class that generates A and AAAA records

        >>> AddressRecord(label=label, domain=domain_object, ip_str=ip_str,
        ... ip_type=ip_type)

    """
    ############################
    # See Ip for all ip fields #
    ############################
    id = models.AutoField(primary_key=True)
    reverse_domain = models.ForeignKey(Domain, null=True, blank=True,
            related_name='addressrecordomain_set')

    class Meta:
        db_table = 'address_record'
        unique_together = ('label', 'domain', 'ip_upper', 'ip_lower',
                'ip_type')
