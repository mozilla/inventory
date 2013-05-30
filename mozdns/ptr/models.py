from django.db import models
from django.core.exceptions import ValidationError


from mozdns.domain.models import name_to_domain
from mozdns.ip.utils import ip_to_domain_name, nibbilize
from mozdns.domain.models import Domain
from mozdns.ip.models import Ip
from mozdns.cname.models import CNAME
from mozdns.ip.utils import ip_to_dns_form
from mozdns.validation import validate_name, validate_ttl
from mozdns.mixins import ObjectUrlMixin, DisplayMixin
from mozdns.models import ViewMixin, TTLRRMixin
from core.interface.static_intr.models import StaticInterface

import reversion

from gettext import gettext as _


class BasePTR(object):
    def clean_reverse(self, update_reverse_domain=True):
        # This indirection is so StaticReg can call this function
        if update_reverse_domain:
            self.update_reverse_domain()
        self.check_for_illegal_rr_ttl(field_name='ip_str')
        self.check_no_ns_soa_condition(self.reverse_domain)
        self.reverse_validate_no_cname()

    def reverse_validate_no_cname(self):
        """
        Considering existing CNAMES must be done when editing and
        creating new :class:`PTR` objects.

            "PTR records must point back to a valid A record, not a
            alias defined by a CNAME."

            -- `RFC 1912 <http://tools.ietf.org/html/rfc1912>`__

        An example of something that is not allowed::

            FOO.BAR.COM     CNAME       BEE.BAR.COM

            BEE.BAR.COM     A           128.193.1.1

            1.1.193.128     PTR         FOO.BAR.COM
            ^-- PTR's shouldn't point to CNAMES
        """
        # There are preexisting records that break this rule. We can't support
        # this requirement until those records are fixed
        return
        if CNAME.objects.filter(fqdn=self.name).exists():
            raise ValidationError(
                "PTR records must point back to a valid A record, not a "
                "alias defined by a CNAME. -- RFC 1034"
            )

    def update_reverse_domain(self):
        # We are assuming that self.clean_ip has been called already
        rvname = nibbilize(self.ip_str) if self.ip_type == '6' else self.ip_str
        rvname = ip_to_domain_name(rvname, ip_type=self.ip_type)
        self.reverse_domain = name_to_domain(rvname)
        if (self.reverse_domain is None or self.reverse_domain.name in
                ('arpa', 'in-addr.arpa', 'ip6.arpa')):
            raise ValidationError(
                "No reverse Domain found for {0} ".format(self.ip_str)
            )

    def rebuild_reverse(self):
        if self.reverse_domain and self.reverse_domain.soa:
            self.reverse_domain.soa.schedule_rebuild()

    def dns_name(self):
        """
        Return the cononical name of this ptr that can be placed in a
        reverse zone file.
        """
        return ip_to_dns_form(self.ip_str)


class PTR(BasePTR, Ip, ViewMixin, ObjectUrlMixin, DisplayMixin):
    """
    A PTR is used to map an IP to a domain name.

    >>> PTR(ip_str=ip_str, name=fqdn, ip_type=ip_type)

    """
    id = models.AutoField(primary_key=True)
    reverse_domain = models.ForeignKey(Domain, null=False, blank=True)

    name = models.CharField(
        max_length=255, validators=[validate_name], help_text="The name that "
        "this record points to."
    )
    ttl = models.PositiveIntegerField(
        default=3600, blank=True, null=True, validators=[validate_ttl]
    )
    description = models.CharField(max_length=1000, null=True, blank=True)
    template = _("{bind_name:$lhs_just} {ttl} {rdclass:$rdclass_just} "
                 "{rdtype:$rdtype_just} {name:1}.")
    search_fields = ('ip_str', 'name')

    class Meta:
        db_table = 'ptr'
        unique_together = ('ip_str', 'ip_type', 'name')

    def __str__(self):
        return "{0} {1} {2}".format(str(self.ip_str), 'PTR', self.name)

    def __repr__(self):
        return "<{0}>".format(str(self))

    @classmethod
    def get_api_fields(cls):
        return ['ip_str', 'ip_type', 'name', 'ttl', 'description']

    @property
    def rdtype(self):
        return 'PTR'

    def save(self, *args, **kwargs):
        urd = kwargs.pop('update_reverse_domain', True)
        self.clean(update_reverse_domain=urd)
        super(PTR, self).save(*args, **kwargs)
        self.rebuild_reverse()

    def delete(self, *args, **kwargs):
        if self.reverse_domain.soa:
            self.reverse_domain.soa.schedule_rebuild()
        super(PTR, self).delete(*args, **kwargs)

    def clean(self, update_reverse_domain=True):
        self.clean_ip()
        # We need to check if there is a registration using our ip and name
        # because that registration will generate a ptr record.
        from core.registration.static.models import StaticReg
        if (StaticReg.objects.filter(
                fqdn=self.name, ip_upper=self.ip_upper,
                ip_lower=self.ip_lower).exists()):
            raise ValidationError(
                "An registration has already used this IP and Name."
            )
        self.clean_reverse(update_reverse_domain=update_reverse_domain)

    def details(self):
        return (
            ('Ip', str(self.ip_str)),
            ('Record Type', 'PTR'),
            ('Name', self.name),
        )

    def bind_render_record(self, pk=False, **kwargs):
        self.fqdn = self.dns_name().strip('.')
        return super(PTR, self).bind_render_record(pk=pk, **kwargs)

reversion.register(PTR)
