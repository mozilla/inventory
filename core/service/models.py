from django.db import models
from django.core.exceptions import ValidationError

from systems.models import Allocation, System

from core.mixins import ObjectUrlMixin
from core.service import constants
from core.utils import to_a, mozillian_a
from core.site.models import Site


class Dependency(models.Model):
    # dependants depend on their providers
    # Django causes an instance's perspective to be a bit strange. The related
    # name of 'dependant' is 'providers' because from an instance's point of
    # view if it is a dependant the object on the other side of the
    # relationship is the provider.
    dependant = models.ForeignKey('Service', related_name='providers')
    provider = models.ForeignKey('Service', related_name='dependants')

    def __str__(self):
        return "<{0}> depends on <{1}>".format(self.dependant, self.provider)


def service_name_validator(name):
    if name.lower == 'none':
        raise ValidationError(
            "The name '{0}' is a reserved service name. You can't user it."
        )


class Service(models.Model, ObjectUrlMixin):
    """
    A service object is used to track a service or to represent a "parent
    service". A service is unique identified by its name and site (where having
    'NULL' for a site is considered a unique value.) By convention, two
    services that have the same name but different sites should be considered
    siblings and should most likely share a common parent site.

    Services can depend on other services. Dependant services are called
    'dependants' and the service being depended on is known as the 'provider'
    service.

    :class:`Allocation` objects and :class:`System` objects can both be
    associated to a service. The cardinatlity of those two relationships is
    many-to-many.
    """
    # Relational fields
    allocations = models.ManyToManyField(Allocation, blank=True)
    systems = models.ManyToManyField(System, blank=True)
    depends_on = models.ManyToManyField(
        'self', through='Dependency', symmetrical=False, blank=True
    )
    parent_service = models.ForeignKey(
        'self', null=True, blank=True, related_name='subservices'
    )
    site = models.ForeignKey(Site, null=True, blank=True)

    # Plain
    name = models.CharField(
        max_length=255, blank=False, validators=[service_name_validator]
    )
    description = models.CharField(max_length=511, blank=True)

    # Autocompleted fields
    category = models.CharField(max_length=255, blank=True)
    business_owner = models.CharField(max_length=255, default='')
    tech_owner = models.CharField(max_length=255, default='')
    used_by = models.CharField(max_length=255, default='')

    # Choice fields
    usage_frequency = models.CharField(
        max_length=255, choices=constants.USAGE_FREQUENCY.items(),
        default='', blank=True
    )
    impact = models.CharField(
        max_length=255, choices=constants.IMPACT.items(), default='',
        blank=True
    )

    # Extra
    notes = models.TextField(blank=True)

    search_fields = (
        'name', 'site__full_name', 'description', 'category', 'tech_owner',
        'used_by'
    )

    @classmethod
    def get_api_fields(cls):
        return [
            'name', 'site', 'description', 'category', 'business_owner',
            'tech_owner', 'used_by', 'usage_frequency', 'impact', 'notes'
        ]

    @property
    def rdtype(self):
        return 'NET'

    class Meta:
        db_table = 'service'

    def __str__(self):
        return "{0} {1}-- Used {2} by {3}".format(
            self.name, '' if not self.site else ' in ' + self.site.full_name,
            constants.USAGE_FREQUENCY[self.usage_frequency.lower()],
            ', '.join(map(str, self.allocations.all()))
        )

    def save(self, *args, **kwargs):
        self.validate_unique()
        self.clean()  # in case we aren't being saved by a form
        super(Service, self).save(*args, **kwargs)

    def clean(self, *args, **kwargs):
        if (
            self.pk and  # we already exist
            self.parent_service and  # we have a parent service
            self.parent_service.pk == self.pk  # our parent service is ourself
        ):
            raise ValidationError("Cannot set parent service to self")

    def validate_unique(self, exclude=None):
        # We can't rely on unique_together for our unique constraint because
        # NULL != NULL in MySQL. That means that a service with name='foo' and
        # site=NULL will not prevent another serivce with name='foo' and
        # site=NULL from being created. Null is the absense of a value so
        # cannot be considered to equal the absense of another value.
        sq = Service.objects.filter(
            site=self.site, name=self.name
        )
        if self.pk:
            sq = sq.exclude(pk=self.pk)

        if sq.exists():
            raise ValidationError(
                "A service with the name '{0}' and site '{1}' already "
                "exists".format(self.name, self.site)
            )

    def details(self):
        r = [
            # Name and site are always present
            ('Name', self.name),
            (
                'Site',
                to_a(self.site.full_name, self.site)
                if self.site else "No site"
            )
        ]
        if self.used_by:
            r.append(('Used By', self.used_by))
        if self.category:
            r.append(('Category', self.category))
        if self.tech_owner:
            r.append(('Tech Owner', mozillian_a(self.tech_owner)))
        if self.business_owner:
            r.append(('Business Owner', mozillian_a(self.business_owner)))
        if self.description:
            r.append(('Description', self.description))
        if self.parent_service:
            r.append((
                'Parent Service',
                to_a(self.parent_service.name, self.parent_service)
            ))

        if self.providers.exists():
            providers = ', '.join([
                to_a(str(d.provider), d.provider)
                for d in self.providers.all()
            ])
            r.append(('Depends on', providers))

        if self.dependants.exists():
            dependants = ', '.join([
                to_a(str(d.dependant), d.dependant)
                for d in self.dependants.all()
            ])
            r.append(('Depended on by', dependants))

        if self.allocations.exists():
            r.append((
                'IT Owners', ', '.join(map(str, self.allocations.all()))
            ))

        return r

    def iql_stmt(self):
        iql_stmt = 'service.name="{0}"'.format(self.name)
        if self.site:
            iql_stmt += ' service.site__full_name="{0}"'.format(
                self.site.full_name
            )
        else:
            iql_stmt += ' service.site=null'

        return iql_stmt

    def __repr__(self):
        return "<Service {0}>".format(self)
