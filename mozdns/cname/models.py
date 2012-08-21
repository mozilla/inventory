from django.db import models
from django.core.exceptions import ValidationError

from mozdns.domain.models import Domain, _name_to_domain
from mozdns.models import MozdnsRecord
from mozdns.validation import validate_name, find_root_domain
from mozdns.search_utils import fqdn_exists


class CNAME(MozdnsRecord):
    """CNAMES can't point to an any other records. Said another way,
    CNAMES can't be at the samle level as any other record. This means
    that when you are creating a CNAME every other record type must be
    checked to make sure that the name about to be taken by the CNAME
    isn't taken by another record. Likewise, all other records must
    check that no CNAME exists with the same name before being created.

    >>> CNAME(label = label, domain = domain, data = data)

    """
    # TODO cite an RFC for that ^ (it's around somewhere)
    id = models.AutoField(primary_key=True)
    data = models.CharField(max_length=100, validators=[validate_name], help_text='CNAME Destination')
    data_domain = models.ForeignKey(Domain, null=True,
                                    related_name='data_domains', blank=True,
                                    on_delete=models.SET_NULL)

    search_fields = ('fqdn', 'data')

    def details(self):
        return  (
                    ('FQDN', self.fqdn),
                    ('Record Type', 'CNAME'),
                    ('Data', self.data),
               )

    class Meta:
        db_table = 'cname'
        unique_together = ('domain', 'label', 'data')

    def save(self, *args, **kwargs):
        # If label, and domain have not changed, don't mark our domain for
        # rebuilding.
        if self.pk:  # We need to exist in the db first.
            db_self = CNAME.objects.get(pk=self.pk)
            if db_self.label == self.label and db_self.domain == self.domain:
                kwargs['no_build'] = False
            else:
                kwargs['no_build'] = True  # Either nothing has changed or
                                        # just data_domain. We want rebuild.
        super(CNAME, self).save(*args, **kwargs)

    def clean(self, *args, **kwargs):
        super(CNAME, self).clean(*args, **kwargs)
        super(CNAME, self).check_for_delegation()
        """The RFC for DNS requires that a CName never be at the same
        level as an SOA, A, or MX record. Bind enforces this
        restriction. When creating a Cname, the UI needs to make sure
        that there are no records of those types that will clash.
        Likewise, when creating an SOA, A or MX, the UI needs to verify
        that there are no MX records at that level.
        """
        # TODO ^
        self.check_SOA_condition()
        self.data_domain = _name_to_domain(self.data)
        self.existing_node_check()

    def __str__(self):
        return "{0} CNAME {1}".format(self.fqdn, self.data)

    def check_SOA_condition(self):
        """We need to check if the domain is the root domain in a zone.
        If the domain is the root domain, it will have an soa, but the
        master domain will have no soa (or it will have a a different
        soa).
        """
        root_domain = find_root_domain(self.domain.soa)
        if root_domain is None:
            return
        if self.fqdn == root_domain.name:
            raise ValidationError("You cannot create a CNAME that points to a"
                                  "domain at the root of a zone.")
        return

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
        qset = fqdn_exists(self.fqdn, cn=False, dn=False, pt=False)
        if qset:
            objects = qset.all()
            raise ValidationError("Objects with this name already exist: {0}".
                                  format(objects))
