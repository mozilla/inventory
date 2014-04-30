from django.db import models
from django.core.exceptions import ValidationError

from string import Template

from mozdns.soa.models import SOA
from mozdns.mixins import ObjectUrlMixin, DisplayMixin
from mozdns.validation import validate_domain_name
from mozdns.validation import do_zone_validation
from mozdns.search_utils import smart_fqdn_exists
from mozdns.ip.utils import ip_to_domain_name, nibbilize
from mozdns.validation import validate_reverse_name
from mozdns.domain.utils import name_to_domain


class Domain(models.Model, ObjectUrlMixin, DisplayMixin):
    """
    A Domain is used as a foreign key for most DNS records.

    A domain's SOA should be shared by only domains within it's zone.

    If two domains are part of different zones, they (and their
    subdomains) will need different SOA objects even if the data contained
    in the SOA is exactly the same. Use the description field to
    distinguish between similar SOAs. This model enforces these
    requirements and will raise a ``ValidationError`` during
    :func:`clean` if it is violated.

    For example: Say we are authoritative for the domains (and zones)
    ``foo.com`` and ``baz.com``.  These zones should have different
    SOA's because they are part of two separate zones. If you had the
    subdomain ``baz.foo.com``, it could have the same SOA as the
    ``foo.com`` domain because it is in the same zone.

    Both 'forward' domains under TLD's like 'com', 'edu', and 'org' and
    'reverse' domains under the TLD's 'in-addr.arpa' and 'ip6.arpa' are stored
    in this table. At first glance it would seem like the two types of domains
    have disjoint data set's; record types that have a Foreign Key back to a
    'reverse' domain would never need to have a Foreign Key back to a 'forward'
    domain. This is not the case. The two main examples are NS and CNAME
    records. If there were two different domain tables, NS/CNAME records would
    need to a) have two different Foriegn Keys, or b) have seperate tables.

    Constraints on both 'forward' and 'reverse' Domains:

        *   A ``ValidationError`` is raised when you try to delete a
            domain that has child domains. A domain should only be deleted when
            it has no child domains.

        *   All domains should have a master (or parent) domain.  A
            ``ValidationError`` will be raised if you try to create an orphan
            domain that should have a master domain.

        *   If you are not authoritative for a reverse domain, set the ``soa``
            field to ``None``.

        *   The ``name`` field must be unique. Failing to make it unique will
            raise a ``ValidationError``.

    Constraints on 'reverse' Domains:

        *   A 'reverse' domain should have ``is_reverse`` set to True.

        *   A 'reverse' domain's name should end in either 'in-addr.arpa' or
            'ip6.arpa'

        *   When a PTR is added it is pointed back to a 'reverse' domain. This
            is done by converting the IP address to the connonical DNS form and
            then doing a longest prefix match against all domains that have
            is_reverse set to True.

    This last point is worth looking at furthur. When adding a new reverse
    domain, all records in the PTR table should be checked for a more
    appropriate domain. Also, when a domain is deleted, all PTR objects should
    be passed down to the parent domain.


    .. warning::

        Deleting a domain will delete all records associated to that domain.
    """

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True,
                            validators=[validate_domain_name])
    master_domain = models.ForeignKey("self", null=True,
                                      default=None, blank=True)
    soa = models.ForeignKey(SOA, null=True, default=None, blank=True)
    is_reverse = models.BooleanField(default=False)
    # This indicates if this domain (and zone) needs to be rebuilt
    dirty = models.BooleanField(default=False)
    # Read about the label and domain paradigm
    purgeable = models.BooleanField(default=False)
    delegated = models.BooleanField(default=False, null=False, blank=True)

    template = "{name:$lhs_just} DOMAIN "

    search_fields = ('name',)

    class Meta:
        db_table = 'domain'

    def __str__(self):
        return "{0}".format(self.name)

    def __repr__(self):
        return "<Domain '{0}'>".format(self.name)

    @property
    def rdtype(self):
        return 'DOMAIN'

    def bind_render_record(self, pk=False, show_ttl=False):
        template = Template(self.template).substitute(**self.justs)
        return template.format(name=self.name)

    def details(self):
        return (
            ('Name', self.name),
            ('Master Domain', self.master_domain),
            ('SOA', self.soa),
            ('Delegated', self.delegated),
        )

    def delete(self, *args, **kwargs):
        self.check_for_children()
        if self.is_reverse:
            self.reassign_reverse_delete()
        if self.has_record_set():
            raise ValidationError("There are records associated with this "
                                  "domain. Delete them before deleting this "
                                  "domain.")
        super(Domain, self).delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        if kwargs.pop('do_full_clean', True):
            self.full_clean()

        if not self.pk:
            new_domain = True
        else:
            new_domain = False
            db_self = Domain.objects.get(pk=self.pk)
            # Raise an exception...
            # If our soa is different AND it's non-null AND we have records in
            # this domain AND EITHER
            #       the new soa has a record domain with no nameservers
            #   OR
            #       it has no root domain, which means we are going to
            #       be the root domain, and we have no nameserver records.
            if (db_self.soa != self.soa and
                self.soa and self.has_record_set() and
                (self.soa.root_domain and
                not self.soa.root_domain.nameserver_set.exists() or
                not self.soa.root_domain and
                 not self.nameserver_set.all().exists())):
                    raise ValidationError("By changing this domain's SOA you "
                                          "are attempting to create a zone "
                                          "whos root domain has no NS record.")
        super(Domain, self).save(*args, **kwargs)
        if self.is_reverse and new_domain:
            # Collect any ptr's that belong to this new domain.
            reassign_reverse_update(self, self.master_domain, self.ip_type())

    def ip_type(self):
        if self.name.endswith('in-addr.arpa'):
            return '4'
        elif self.name.endswith('ip6.arpa'):
            return '6'
        else:
            return None

    def clean(self, ignore_conflicts=False):
        if self.name.endswith('arpa'):
            self.is_reverse = True
        self.master_domain = name_to_master_domain(self.name)

        if not self.master_domain and self.name in ('reverse', 'config'):
            # Right now zone files get placed into invzones/ where directories
            # corresponding to TLDs are placed. There are also directories
            # invzones/config/ (where configs are stored) and invzones/reverse/
            # (where reverse zones are stored) -- we don't want to clobber
            # these directories with TLD directories.
            raise ValidationError(
                "{0} is a reserved TLD name".format(self.name)
            )

        do_zone_validation(self)
        # TODO, can we remove this?
        if self.pk is None and not ignore_conflicts:
            # The object doesn't exist in the db yet. Make sure we don't
            # conflict with existing objects. We may want to move to a more
            # automatic solution where the creation of a new domain will
            # automatically move objects around (see the ensure_domain
            # function).
            qset = smart_fqdn_exists(self.name)
            if qset:
                objects = qset.all()
                raise ValidationError("Objects with this name already "
                                      "exist {0}".format(objects))
        elif self.pk is not None:
            db_self = Domain.objects.get(pk=self.pk)
            if db_self.name != self.name and self.domain_set.exists():
                raise ValidationError("Child domains rely on this domain's "
                                      "name remaining the same.")

    def check_for_children(self):
        if self.domain_set.exists():
            raise ValidationError("Before deleting this domain, please "
                                  "remove it's children.")

    def has_record_set(self, view=None, exclude_ns=False):
        object_sets = [
            self.addressrecord_set,
            self.cname_set,
            self.mx_set,
            self.srv_set,
            self.sshfp_set,
            self.staticreg_set,
            self.reverse_staticreg_set,
            self.txt_set,
            self.ptr_set
        ]
        if not view:
            for object_set in object_sets:
                if object_set.exists():
                    return True
            if not exclude_ns and self.nameserver_set.exists():
                return True
        else:
            for object_set in object_sets:
                if object_set.filter(views=view).exists():
                    return True
            if (not exclude_ns and
                    self.nameserver_set.filter(views=view).exists()):
                return True

        return False

    ### Reverse Domain Functions
    def reassign_reverse_delete(self):
        """
        This function serves as a pretty subtle workaround.

            *   An Ip is not allowed to have a reverse_domain of None.

            *   When you save an Ip it is automatically assigned the most
                appropriate reverse_domain

        Passing the update_reverse_domain as False will by pass the Ip's
        class attempt to find an appropriate reverse_domain. This way
        you can reassign the reverse_domain of an Ip, save it, and then
        delete the old reverse_domain.
        """
        def reassign(objs):
            for obj in objs:
                obj.reverse_domain = self.master_domain
                obj.save(update_reverse_domain=False)

        reassign(self.ptr_set.iterator())
        reassign(self.reverse_staticreg_set.iterator())

    def get_history_url(self):
        # domains don't use reversion
        return '/core/search/'


def boot_strap_ipv6_reverse_domain(ip, soa=None):
    """
    This function is here to help create IPv6 reverse domains.

    .. note::
        Every nibble in the reverse domain should not exists for this
        function to exit successfully.


    :param ip: The ip address in nibble format
    :type ip: str
    :raises: ReverseDomainNotFoundError
    """
    validate_reverse_name(ip, '6')

    for i in xrange(1, len(ip) + 1, 2):
        cur_reverse_domain = ip[:i]
        domain_name = ip_to_domain_name(cur_reverse_domain, ip_type='6')
        reverse_domain = Domain(name=domain_name)
        reverse_domain.soa = soa
        reverse_domain.save()
    return reverse_domain


def reassign_reverse_update(reverse_domain_1, reverse_domain_2, ip_type):
    """
    There are some formalities that need to happen when a reverse
    domain is added or deleted. For example, when adding say we had the
    ip address 128.193.4.0 and it had the reverse_domain 128.193. If we
    add the reverse_domain 128.193.4, our 128.193.4.0 no longer belongs
    to the 128.193 domain. We need to re-asign the ip to it's correct
    reverse domain.

    :param reverse_domain_1: The domain which could possibly have
        addresses added to it.

    :type reverse_domain_1: :class:`Domain`

    :param reverse_domain_2: The domain that has ip's which might not
        belong to it anymore.

    :type reverse_domain_2: :class:`Domain`
    """

    if reverse_domain_2 is None or ip_type is None:
        return

    def reassign(objs):
        for obj in objs:
            if ip_type == '6':
                nibz = nibbilize(obj.ip_str)
                revname = ip_to_domain_name(nibz, ip_type='6')
            else:
                revname = ip_to_domain_name(obj.ip_str, ip_type='4')
            correct_reverse_domain = name_to_domain(revname)
            if correct_reverse_domain != obj.reverse_domain:
                # TODO, is this needed? The save() function (actually the
                # clean_ip function) will assign the correct reverse domain.
                obj.reverse_domain = correct_reverse_domain
                obj.save()

    ptrs = reverse_domain_2.ptr_set.iterator()
    sregs = reverse_domain_2.reverse_staticreg_set.iterator()

    reassign(ptrs)
    reassign(sregs)


# A bunch of handy functions that would cause circular dependencies if
# they were in another file.
def name_to_master_domain(name):
    """
    Given an domain name, this function returns the appropriate
    master domain.

    :param name: The domain for which we are using to search for a
        master domain.
    :type name: str
    :returns: domain -- Domain object
    :raises: ValidationError
    """
    tokens = name.split('.')
    master_domain = None
    for i in reversed(xrange(len(tokens) - 1)):
        parent_name = '.'.join(tokens[i + 1:])
        possible_master_domain = Domain.objects.filter(name=parent_name)
        if not possible_master_domain:
            raise ValidationError("Master Domain for domain {0}, not "
                                  "found.".format(name))
        else:
            master_domain = possible_master_domain[0]
    return master_domain


def _name_to_domain(fqdn):
    return name_to_domain(fqdn)
