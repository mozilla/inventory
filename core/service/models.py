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
    if not name:
        raise ValidationError("A services name cannot be empty")
    if name.lower == 'none':
        raise ValidationError(
            "The name '{0}' is a reserved service name. You can't use it."
        )


class Service(models.Model, ObjectUrlMixin):
    """
    A service object is used to track a service or to represent a "parent
    service". A service is uniquely identified by its name and site (where
    having 'NULL' for a site is considered a unique value.) By convention, two
    services that have the same name but different sites should be considered
    siblings and should most likely share a common parent service.

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
    alias = models.CharField(max_length=511, blank=True)
    description = models.CharField(max_length=511, blank=True)

    # Autocompleted fields
    category = models.CharField(max_length=255, blank=True)
    business_owner = models.CharField(max_length=255, default='', blank=True)
    tech_owner = models.CharField(max_length=255, default='', blank=True)
    used_by = models.CharField(max_length=255, default='', blank=True)

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
        'name', 'alias', 'site__full_name', 'description', 'category',
        'tech_owner', 'used_by'
    )

    @classmethod
    def get_api_fields(cls):
        return [
            'name', 'alias', 'site', 'description', 'category',
            'business_owner', 'tech_owner', 'used_by', 'usage_frequency',
            'impact', 'notes'
        ]

    @property
    def rdtype(self):
        return 'NET'

    class Meta:
        db_table = 'service'

    def __str__(self):
        s = "{0}{1} ".format(
            self.name, '' if not self.site else ' in ' + self.site.full_name
        )
        s += "-- Used {0}".format(
            constants.USAGE_FREQUENCY[self.usage_frequency.lower()]
        )
        a_str = self.get_allocations_str()
        if a_str:
            s += " by " + a_str
        return s

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

    def get_attr(self, attr_name):
        if (
            not getattr(self, attr_name) and
            self.parent_service and
            getattr(self.parent_service, attr_name)
        ):
            return "{0} (inherited from parent service)".format(
                getattr(self.parent_service, attr_name)
            )
        else:
            return getattr(self, attr_name)

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
        if self.alias:
            r.append(('Alias', self.get_attr('alias')))
        if self.used_by:
            r.append(('Used By', self.get_attr('used_by')))
        if self.category:
            r.append(('Category', self.get_attr('category')))
        if self.tech_owner:
            r.append(('Tech Owner', mozillian_a(self.get_attr('tech_owner'))))
        if self.business_owner:
            r.append((
                'Business Owner',
                mozillian_a(self.get_attr('business_owner'))
            ))
        if self.description:
            r.append(('Description', self.get_attr('description')))
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
            r.append(('IT Owners', self.get_allocations_str()))

        return r

    def get_allocations_str(self):
        return ', '.join(map(str, self.allocations.all()))

    def iql_stmt(self):
        iql_stmt = "service.name='{0}'".format(self.name)
        if self.site:
            iql_stmt += " service.site__full_name='{0}'".format(
                self.site.full_name
            )
        else:
            iql_stmt += ' service.site=null'

        return iql_stmt

    def __repr__(self):
        return "<Service {0}>".format(self)

    @classmethod
    def export_services(cls, services, fields=None):
        ret = []
        # site is relational and needs to be handled specially
        fields = fields or cls.get_api_fields()

        if 'site' in fields:
            fields.remove('site')

        for service in services:
            # create a service dict
            sd = dict((field, getattr(service, field)) for field in fields)
            sd['systems'] = list(service.systems.all().values_list(
                'hostname', flat=True
            ))
            sd['site'] = service.site.full_name if service.site else 'None'

            sd['parent_service'] = (
                service.parent_service.iql_stmt()
                if service.parent_service else 'None'
            )

            for ds in service.providers.all():
                # Append an IQL statement that uniqly identifies a service
                sd.setdefault('depends_on', []).append(ds.provider.iql_stmt())

            ret.append(sd)
        return ret

    @classmethod
    def iql_to_service(cls, iql_stmt, bad_iql_error=None,
                       no_services_error=None, ambiguous_error=None):
        # Note: there is an import loop in the global scope
        from core.search.compiler.django_compile import search_type
        services, error = search_type(iql_stmt, 'SERVICE')
        if error:
            raise bad_iql_error or ValueError(
                "When resolving IQL '{0}' got error "
                "'{1}'".format(iql_stmt, error)
            )

        if not services:
            raise no_services_error or ValueError(
                "When resolving IQL '{0}' no services were found"
                .format(iql_stmt)
            )

        if len(services) > 1:
            raise ambiguous_error or ValueError(
                "When resolving IQL '{0}' multiple services were returned"
                .format(iql_stmt)
            )

        return services[0]

    def service_import_set_systems(self, hostnames):
        # Note: Make sure to call save() after calling this function
        self.systems.clear()
        for hostname in hostnames:
            try:
                system = System.objects.get(hostname=hostname)
            except System.DoesNotExist:
                raise System.DoesNotExist(
                    "The system with hostname '{0}' does not "
                    "exist".format(hostname)
                )
            self.systems.add(system)

    def service_import_set_depends_on(self, dependencies):
        # Note: Make sure to call save() after calling this function
        # XXX: does clear() actually delete the dependencies?
        # Either it needs to or we need to do that manually...
        self.depends_on.clear()
        for dep in dependencies:
            dep_service = Service.iql_to_service(
                dep,
                no_services_error=ValueError(
                    "When adding a dependency for '{0}', could "
                    "not find a service corresponding to "
                    "'{1}'".format(self.iql_stmt(), dep)
                ),
                ambiguous_error=ValueError(
                    "When adding a dependency for '{0}', found "
                    "multiple services correspond to "
                    "'{1}'".format(self.iql_stmt(), dep)
                )
            )
            Dependency.objects.get_or_create(
                dependant=self, provider=dep_service
            )

    def service_import_set_field(self, field_name, value):
        # Note: Make sure to call save() after calling this function
        opts = self._meta
        f = opts.get_field_by_name(field_name)
        if not f:
            raise ValueError(
                "The service '{0}' doesn't have a field "
                "'{1}'".format(self.iql_stmt(), field_name)
            )
        field = f[0]

        if (
            hasattr(field, 'choices') and  # check for a choices
            field.choices and  # are there restrictions?
            value not in [v[0] for v in field.choices]  # is it a valid choice?
        ):
            raise ValueError(
                "The value '{0}' isn't a valid choice for the '{1}' field"
                .format(value, field_name)
            )

        setattr(self, field_name, value)

    def service_import_set_parent_service(self, parent_service_iql):
        # Note: Make sure to call save() after calling this function
        try:
            if not parent_service_iql or parent_service_iql.title() == 'None':
                self.parent_service = None
            else:
                self.parent_service = Service.iql_to_service(
                    parent_service_iql
                )
        except Service.DoesNotExist:
            raise Service.DoesNotExist(
                "The service with name '{0}' does not "
                "exist".format(parent_service_iql)
            )

    def service_import_set_site(self, site_name):
        try:
            if not site_name or site_name.title() == 'None':
                site = None
            else:
                site = Site.objects.get(full_name=site_name)
        except Site.DoesNotExist:
            raise System.DoesNotExist(
                "The site with name '{0}' does not exist".format(site_name)
            )

        self.site = site

    @classmethod
    def import_services(cls, services):
        """
        Import a json blob that has the same format generated by the
        Service.export_services function. This function may raise a
        System.DoesNotExist, Service.DoesNotExist, ValueError, or
        Site.DoesNotExist excpetion. The caller should handle these accordingly

        This function does not manage transactions itself but should probably
        be ran in a transaction
        """
        for service_blob in services:
            try:
                site = service_blob.get('site', None)
                if site:
                    site = Site.objects.get(full_name=site)
                service, created = Service.objects.get_or_create(
                    name=service_blob.get('name', ''),
                    site=site
                )
            except Service.DoesNotExist:
                raise System.DoesNotExist(
                    "The service with name '{0}' does not "
                    "exist".format(service_blob['name'])
                )
            except Site.DoesNotExist:
                raise System.DoesNotExist(
                    "The service with name '{0}' is asking for a site '{1}' "
                    "that does not exist".format(
                        service_blob.get('name', 'None'),
                        service_blob.get('site', 'None')
                    )
                )

            # set all the fields on the service we are importing
            for field, value in service_blob.iteritems():
                if field == 'systems':
                    service.service_import_set_systems(value)
                elif field == 'parent_service':
                    service.service_import_set_parent_service(value)
                elif field == 'site':
                    service.service_import_set_site(value)
                elif field == 'pk':
                    # lets not let the user shoot themselves in the foot
                    continue
                elif field == 'depends_on':
                    service.service_import_set_depends_on(value)
                else:
                    service.service_import_set_field(field, value)

            service.save()
