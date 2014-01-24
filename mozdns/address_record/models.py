from django.db import models
from django.core.exceptions import ValidationError

import mozdns
from mozdns.cname.models import CNAME
from mozdns.ip.models import Ip
from mozdns.models import MozdnsRecord, LabelDomainMixin

import reversion


class BaseAddressRecord(Ip, MozdnsRecord):
    """
    AddressRecord is the class that generates A and AAAA records

        >>> AddressRecord(label=label, domain=domain_object, ip_str=ip_str,
        ... ip_type=ip_type)

    """
    search_fields = ("fqdn", "ip_str")

    class Meta:
        abstract = True

    @property
    def rdtype(self):
        if self.ip_type == '6':
            return 'AAAA'
        return 'A'

    def details(self):
        return (
            ("FQDN", self.fqdn),
            ("Record Type", self.record_type()),
            ("IP", str(self.ip_str)),
        )

    @classmethod
    def get_api_fields(cls):
        return super(BaseAddressRecord, cls).get_api_fields() + [
            'ip_str', 'ip_type'
        ]

    def clean(self, *args, **kwargs):
        self.clean_ip()
        ignore_sreg = kwargs.pop("ignore_sreg", False)
        validate_glue = kwargs.pop("validate_glue", True)

        super(BaseAddressRecord, self).clean(*args, **kwargs)

        if validate_glue:
            self.check_glue_status()
        if not ignore_sreg:
            self.check_sreg_collision()

    def check_sreg_collision(self):
        from core.registration.static.models import StaticReg
        if StaticReg.objects.filter(
                fqdn=self.fqdn, ip_upper=self.ip_upper,
                ip_lower=self.ip_lower).exists():
            raise ValidationError(
                "A Static Registration has already reserved this A record."
            )

    def delete(self, *args, **kwargs):
        """
        Address Records that are glue records or that are pointed to
        by a CNAME should not be removed from the database.
        """
        if kwargs.pop("validate_glue", True):
            if self.nameserver_set.exists():
                raise ValidationError(
                    "Cannot delete the record {0}. It is a glue "
                    "record.".format(self.record_type())
                )
        if kwargs.pop("check_cname", True):
            # If there is a cname pointing at us and there is no other address
            # record that it could be pointing at, fail to be deleted.
            if (CNAME.objects.filter(target=self.fqdn).exists() and
                    not self.__class__.objects.filter(fqdn=self.fqdn)
                    .exclude(pk=self.pk).exists()):
                raise ValidationError(
                    "A CNAME points to this {0} record. Change the CNAME "
                    "before deleting this record.".format(self.record_type())
                )

        super(BaseAddressRecord, self).delete(*args, **kwargs)

    def validate_delegation_conditions(self):
        """
        If our domain is delegated then an A record can only have a
        name that is the same as a nameserver in that domain (glue).
        """
        if not (self.domain and self.domain.delegated):
            return
        if self.domain.nameserver_set.filter(server=self.fqdn).exists():
            return
        else:
            # Confusing error messege?
            raise ValidationError(
                "You can only create an A records in a delegated domain that "
                "has an NS record pointing at it."
            )

    def check_glue_status(self):
        """
        If this record is a "glue" record for a Nameserver instance,
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
            raise ValidationError(
                "This record is a glue record for a Nameserver. Change the "
                "Nameserver to edit this record."
            )

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


class AddressRecord(BaseAddressRecord, LabelDomainMixin):
    """
    AddressRecord is the class that generates A and AAAA records

        >>> AddressRecord(label=label, domain=domain_object, ip_str=ip_str,
        ... ip_type=ip_type)

    """
    ############################
    # See Ip for all ip fields #
    ############################
    id = models.AutoField(primary_key=True)

    template = ("{bind_name:$lhs_just} {ttl_} {rdclass:$rdclass_just} "
                "{rdtype:$rdtype_just} {ip_str:$rhs_just}")

    class Meta:
        db_table = "address_record"
        unique_together = (
            "label", "domain", "fqdn", "ip_upper", "ip_lower", "ip_type"
        )


reversion.register(AddressRecord)
