from django.db import models
from django.core.exceptions import ValidationError, ObjectDoesNotExist

import mozdns
from mozdns.models import MozdnsRecord, LabelDomainMixin
from mozdns.validation import validate_name
from mozdns.search_utils import smart_fqdn_exists

import reversion

from gettext import gettext as _


class CNAME(MozdnsRecord, LabelDomainMixin):
    """CNAMES can't point to an any other records. Said another way,
    CNAMES can't be at the samle level as any other record. This means
    that when you are creating a CNAME every other record type must be
    checked to make sure that the name about to be taken by the CNAME
    isn't taken by another record. Likewise, all other records must
    check that no CNAME exists with the same name before being created.

    >>> CNAME(label = label, domain = domain, target = target)

    """
    # TODO cite an RFC for that ^ (it's around somewhere)
    id = models.AutoField(primary_key=True)
    target = models.CharField(max_length=100, validators=[validate_name],
                              help_text="CNAME Target")
    template = _("{bind_name:$lhs_just} {ttl} {rdclass:$rdclass_just} "
                 "{rdtype:$rdtype_just} {target:$rhs_just}.")

    search_fields = ('fqdn', 'target')

    def details(self):
        return (
            ('FQDN', self.fqdn),
            ('Record Type', 'CNAME'),
            ('Target', self.target),
        )

    class Meta:
        db_table = 'cname'
        unique_together = ('domain', 'label', 'target')

    @property
    def rdtype(self):
        return 'CNAME'

    @classmethod
    def get_api_fields(cls):
        return super(CNAME, cls).get_api_fields() + ['target']

    def save(self, *args, **kwargs):
        self.clean()
        super(CNAME, self).save(*args, **kwargs)

    def clean(self, *args, **kwargs):
        super(CNAME, self).clean(*args, **kwargs)
        if self.fqdn == self.target:
            raise ValidationError("CNAME loop detected.")
        self.check_SOA_condition()
        self.existing_node_check()

    def __str__(self):
        return "{0} CNAME {1}".format(self.fqdn, self.target)

    def check_SOA_condition(self):
        """We need to check if the domain is the root domain in a zone.
        If the domain is the root domain, it will have an soa, but the
        master domain will have no soa (or it will have a a different
        soa).
        """
        try:
            self.domain
        except ObjectDoesNotExist:
            return  # Validation will fail eventually
        if not self.domain.soa:
            return
        root_domain = self.domain.soa.root_domain
        if root_domain is None:
            return
        if self.fqdn == root_domain.name:
            raise ValidationError("You cannot create a CNAME who's left hand "
                                  "side is at the same level as an SOA")

    def existing_node_check(self):
        """Make sure no other nodes exist at the level of this CNAME.

            "If a CNAME RR is present at a node, no other data should be
            present; this ensures that the data for
            a canonical name and its aliases cannot be different."

            -- `RFC 1034 <http://tools.ietf.org/html/rfc1034>`_

        For example, this would be bad::

            FOO.BAR.COM     CNAME       BEE.BAR.COM

            BEE.BAR.COM     A           128.193.1.1

            FOO.BAR.COM     TXT         "v=spf1 include:foo.com -all"

        If you queried the ``FOO.BAR.COM`` name, the class of the record
        that would be returned would be ambiguous.



        .. note::
            The following records classes are checked.
                * :class:`AddressRecord` (A and AAAA)
                * :class:`SRV`
                * :class:`TXT`
                * :class:`MX`
        """
        qset = smart_fqdn_exists(self.fqdn, cn=False)
        if qset:
            objects = qset.all()
            raise ValidationError("Objects with this name already exist: {0}".
                                  format(objects))
        MX = mozdns.mx.models.MX
        if MX.objects.filter(server=self.fqdn):
            raise ValidationError("RFC 2181 says you shouldn't point MX "
                                  "records at CNAMEs and an MX points to"
                                  " this name!")
        # There are preexisting records that break this rule. We can't support
        # this requirement until those records are fixed
        # PTR = mozdns.ptr.models.PTR
        # if PTR.objects.filter(name=self.fqdn):
        #    raise ValidationError("RFC 1034 says you shouldn't point PTR "
        #                          "records at CNAMEs, and a PTR points to"
        #                          " this name!")

        # Should SRV's not be allowed to point to a CNAME? /me looks for an RFC

reversion.register(CNAME)
