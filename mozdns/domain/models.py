from django.db import models
from django.core.exceptions import ValidationError

import mozdns
from mozdns.soa.models import SOA
from mozdns.mixins import ObjectUrlMixin
from mozdns.validation import validate_domain_name, _name_type_check
from mozdns.validation import do_zone_validation
from mozdns.search_utils import fqdn_exists


class Domain(models.Model, ObjectUrlMixin):
    """A Domain is used as a foreign key for most DNS records.

    A domain's SOA should be shared by only domains within it's zone.

    If two domains are part of different zones, they (and their
    subdomains) will need different SOA objects even if the data
    contained in the SOA is exactly the same. Use the comment field to
    distinguish between similar SOAs. Mozder enforces this condition and
    will raise a ``ValidationError`` during ``clean_all`` if it is
    violated.

    For example: Say you are authoritative for the domains (and zones)
    ``foo.com`` and ``baz.com``.  These zones should have different
    SOA's because they are part of two separate zones. If you had the
    subdomain ``baz.foo.com``, it could have the same SOA as the
    ``foo.com`` domain because it is in the same zone.
    """

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True,
                            validators=[validate_domain_name])
    master_domain = models.ForeignKey("self", null=True,
                                      default=None, blank=True)
    soa = models.ForeignKey(SOA, null=True, default=None, blank=True)
    # This indicates if this domain (and zone) needs to be rebuilt
    dirty = models.BooleanField(default=False)
    delegated = models.BooleanField(default=False, null=False, blank=True)

    class Meta:
        db_table = 'domain'

    def details(self):
        return (
            ('Name', self.name),
            ('Master Domain', self.master_domain),
            ('SOA', self.soa),
            ('Delegated', self.delegated),
        )

    def delete(self, *args, **kwargs):
        self.check_for_children()
        self.reassign_data_domains()
        super(Domain, self).delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.full_clean()
        super(Domain, self).save(*args, **kwargs)
        self.look_for_data_domains()  # This needs to come after super's
        # save becase when a domain is first created it is not in the db.
        # look_for_data_domains relies on the domain having a pk.

    def clean(self):
        self.master_domain = _name_to_master_domain(self.name)
        do_zone_validation(self)
        if self.pk is None:
            # The object doesn't exist in the db yet. Make sure we don't
            # conflict with existing objects.
            qset = fqdn_exists(self.name, pt=False)
            if qset:
                objects = qset.all()
                raise ValidationError("Objects with this name already "
                                      "exist {0}".format(objects))

    def __str__(self):
        return "{0}".format(self.name)

    def __repr__(self):
        return "<Domain '{0}'>".format(self.name)

    def check_for_children(self):
        if self.domain_set.all().exists():
            raise ValidationError("Before deleting this domain, please "
                                  "remove it's children.")

    def look_for_data_domains(self):
        """When a domain is created, look for CNAMEs and PTRs that could
        have data domains in this domain."""
        if self.master_domain:
            ptrs = self.master_domain.ptr_set.all()
            cnames = self.master_domain.data_domains.all()
        else:
            CNAME = mozdns.cname.models.CNAME
            PTR = mozdns.ptr.models.PTR
            cnames = CNAME.objects.filter(data_domain=None)
            ptrs = PTR.objects.filter(data_domain=None)

        for ptr in ptrs:
            ptr.data_domain = _name_to_domain(ptr.name)
            ptr.save()

        for cname in cnames:
            cname.data_domain = _name_to_domain(cname.data)
            cname.save()




    def reassign_data_domains(self):
        """:class:`PTR`s and :class:`CNAME`s keep track of which domain
        their data is pointing to. This function reassign's those data
        domains to the data_domain's master domain."""

        for ptr in self.ptr_set.all():
            if ptr.data_domain.master_domain:
                ptr.data_domain = ptr.data_domain.master_domain
            else:
                ptr.data_domain = None
            ptr.save()

        for cname in self.data_domains.all():
            if cname.data_domain.master_domain:
                cname.data_domain = cname.data_domain.master_domain
            else:
                cname.data_domain = None
            cname.save()

# A bunch of handy functions that would cause circular dependencies if
# they were in another file.
def _name_to_master_domain(name):
    """Given an domain name, this function returns the appropriate
    master domain.

    :param name: The domain for which we are using to search for a
    master domain.
    :type name: str
    :returns: domain -- Domain object
    :raises: ValidationError
    """
    tokens = name.split('.')
    master_domain = None
    for i in reversed(range(len(tokens) - 1)):
        parent_name = '.'.join(tokens[i + 1:])
        possible_master_domain = Domain.objects.filter(name=parent_name)
        if not possible_master_domain:
            raise ValidationError("Master Domain for domain {0}, not "
                                  "found.".format(name))
        else:
            master_domain = possible_master_domain[0]
    return master_domain


def _name_to_domain(fqdn):
    _name_type_check(fqdn)
    labels = fqdn.split('.')
    for i in range(len(labels)):
        name = '.'.join(labels[i:])
        longest_match = Domain.objects.filter(name=name)
        if longest_match:
            return longest_match[0]
    return None


def _check_TLD_condition(record):
    domain = Domain.objects.filter(name=record.fqdn)
    if not domain:
        return
    if record.label == '' and domain[0] == record.domain:
        return  # This is allowed
    else:
        raise ValidationError("You cannot create an record that points "
                              "to the top level of another domain.")
