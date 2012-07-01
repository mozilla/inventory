from django.db import models
from django.core.exceptions import ValidationError

from mozdns.view.models import View
from mozdns.domain.models import Domain, _name_to_domain
from mozdns.ip.models import Ip
from mozdns.validation import validate_name
from mozdns.mixins import ObjectUrlMixin
from core.interface.static_intr.models import StaticInterface

import pdb

class PTR(Ip, ObjectUrlMixin):
    """A PTR is used to map an IP to a domain name.

    >>> PTR(ip_str=ip_str, name=fqdn, ip_type=ip_type)

    """
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, validators=[validate_name])
    reverse_domain = models.ForeignKey(Domain, null=False, blank=True)
    data_domain = models.ForeignKey(Domain, null=True, blank=True,
            related_name='ptrs')
    views = models.ManyToManyField(View)

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
        if self.pk:  # We need to exist in the db first.
            db_self = PTR.objects.get(pk=self.pk)
            if db_self.name == self.name and db_self.ip_str == self.ip_str:
                # Nothing important changed. Don't rebuild the zone file.
                rebuild = False
            else:
                rebuild = True
        else:
            rebuild = True

        if rebuild:
            self.reverse_domain.dirty = True
            self.reverse_domain.save()  # The reverse_domain field is in the Ip
                                        # class.
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
        # We need to check if there is an interface using our ip and name
        # because that interface will generate a ptr record.
        if (StaticInterface.objects.filter(fqdn=self.name,
            ip_str=self.ip_str).exists()):
            raise ValidationError("An Interface has already used this IP and "
                "Name.")
        if 'update_reverse_domain' in kwargs:  # TODO, clean this up
            urd = kwargs.pop('update_reverse_domain')
            self.clean_ip(update_reverse_domain=urd)
        else:
            self.clean_ip()
        self.data_domain = _name_to_domain(self.name)

    def __str__(self):
        return "{0} {1} {2}".format(str(self.ip_str), 'PTR', self.name)

    def __repr__(self):
        return "<{0}>".format(str(self))
