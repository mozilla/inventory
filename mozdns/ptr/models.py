from django.db import models
from django.core.exceptions import ValidationError

from mozdns.view.models import View
from mozdns.domain.models import Domain, _name_to_domain
from mozdns.ip.models import Ip
from mozdns.ip.utils import ip_to_dns_form
from mozdns.validation import validate_name, validate_ttl
from mozdns.validation import validate_views
from mozdns.mixins import ObjectUrlMixin
from core.interface.static_intr.models import StaticInterface

import pdb


class PTR(Ip, ObjectUrlMixin):
    """A PTR is used to map an IP to a domain name.

    >>> PTR(ip_str=ip_str, name=fqdn, ip_type=ip_type)

    """
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, validators=[validate_name],
                help_text="The name that this record points to.")
    ttl = models.PositiveIntegerField(default=3600, blank=True, null=True,
            validators=[validate_ttl])
    reverse_domain = models.ForeignKey(Domain, null=False, blank=True)
    data_domain = models.ForeignKey(Domain, null=True, blank=True,
            related_name='ptrs', on_delete=models.SET_NULL)
    views = models.ManyToManyField(View, blank=True)
    comment = models.CharField(max_length=1000, null=True, blank=True)

    search_fields = ('ip_str', 'name')

    @classmethod
    def get_api_fields(cls):
        return ['ip_str', 'ip_type', 'name', 'ttl', 'comment']

    def details(self):
        return (
                    ('Ip', str(self.ip_str)),
                    ('Record Type', 'PTR'),
                    ('Name', self.name),
               )

    class Meta:
        db_table = 'ptr'
        unique_together = ('ip_str', 'ip_type', 'name')

    def save(self, *args, **kwargs):
        if self.reverse_domain and self.reverse_domain.soa:
            self.reverse_domain.soa.dirty = True
            self.reverse_domain.soa.save()
            # The reverse_domain field is in the Ip class.
        super(PTR, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        super(PTR, self).delete(*args, **kwargs)

    def validate_no_cname(self):
        """Considering existing CNAMES must be done when editing and
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
        pass
        #TODO, impliment this function and call it in clean()

    def clean(self, *args, **kwargs):
        urd = kwargs.pop('update_reverse_domain', True)
        self.clean_ip(update_reverse_domain=urd)
        self.data_domain = _name_to_domain(self.name)
        # We need to check if there is an interface using our ip and name
        # because that interface will generate a ptr record.
        if (StaticInterface.objects.filter(fqdn=self.name,
            ip_upper=self.ip_upper, ip_lower=self.ip_lower).exists()):
            raise ValidationError("An Interface has already used this IP and "
                "Name.")

    def __str__(self):
        return "{0} {1} {2}".format(str(self.ip_str), 'PTR', self.name)

    def __repr__(self):
        return "<{0}>".format(str(self))

    def dns_name(self):
        """Return the cononical name of this ptr that can be placed in a
        reverse zone file."""
        return ip_to_dns_form(self.ip_str, ip_type=self.ip_type)


