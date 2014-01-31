from django.db import models
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse

from core.mixins import ObjectUrlMixin, CoreDisplayMixin
from core.keyvalue.models import KeyValue
from core.utils import networks_to_Q, to_a
from core.validation import validate_site_name
from core.keyvalue.utils import AuxAttr


class Site(models.Model, ObjectUrlMixin, CoreDisplayMixin):
    systems = None
    # This is memoized later. Remove it when SystemRack is moved into it's own
    # file as this circular import is not required.

    id = models.AutoField(primary_key=True)
    full_name = models.CharField(
        max_length=255, null=True, blank=True
    )
    name = models.CharField(
        max_length=255, validators=[validate_site_name], blank=True
    )
    parent = models.ForeignKey("self", null=True, blank=True)

    search_fields = ('full_name',)

    template = (
        "{full_name:$lhs_just} {rdtype:$rdtype_just} {full_name:$rhs_just}"
    )

    class Meta:
        db_table = 'site'
        unique_together = ('full_name',)

    def __str__(self):
        return "{0}".format(self.full_name)

    def __repr__(self):
        return "<Site {0}>".format(self)

    @classmethod
    def get_api_fields(cls):
        return ['name', 'parent', 'full_name']

    @property
    def rdtype(self):
        return 'SITE'

    def save(self, *args, **kwargs):
        self.name = self.full_name.split('.')[0]
        self.full_clean()
        super(Site, self).save(*args, **kwargs)

    def clean(self):
        map(validate_site_name, self.full_name.split('.'))
        self.name, parent_name = (
            self.full_name.split('.')[0], self.full_name.split('.')[1:]
        )
        validate_site_name(self.name)
        if self.pk:
            db_self = self.__class__.objects.get(pk=self.pk)
            if self.site_set.exists() and self.name != db_self.name:
                raise ValidationError(
                    "This site has child sites. You cannot change it's name "
                    "without affecting all child sites."
                )
        if not self.full_name.find('.') == -1:
            self.parent, _ = self.__class__.objects.get_or_create(
                full_name='.'.join(parent_name)
            )
        else:
            self.parent = None

    def delete(self, *args, **kwargs):
        if self.site_set.all().exists():
            raise ValidationError(
                "This site has child sites. You cannot delete it."
            )
        super(Site, self).delete(*args, **kwargs)

    def update_attrs(self):
        self.attrs = AuxAttr(SiteKeyValue, self)

    def details(self):
        details = [
            ('Name', self.full_name),
        ]
        if self.parent:
            details.append(
                ('Parent Site', to_a(self.parent.full_name, self.parent))
            )
        else:
            details.append(
                ('All sites', to_a('Global Site View', reverse('site-list'),
                                   use_absolute_url=False))
            )
        return details

    def compile_Q(self):
        """Compile a Django Q that will match any IP inside this site."""
        return networks_to_Q(self.network_set.all())

    def get_site_path(self):
        target = self
        npath = [self.name]
        while True:
            if target.parent is None:
                break
            else:
                npath.append(target.parent.name)
                target = target.parent
        return '.'.join(npath)

    def get_systems(self):
        """Get all systems associated to racks in this site"""
        if not self.systems:
            from systems.models import System
            self.systems = System.objects.all()
        return self.systems.filter(system_rack__in=self.systemrack_set.all())

    def get_allocated_networks(self):
        """Return a list of all top level networks assocaited with this site"""
        from core.network.utils import calc_top_level_networks
        return calc_top_level_networks(self)


class SiteKeyValue(KeyValue):
    obj = models.ForeignKey(Site, related_name='keyvalue_set', null=False)

    class Meta:
        db_table = 'site_key_value'
        unique_together = ('key', 'value', 'obj')

    def _aa_address(self):
        """
        The address of this site.
        """
        return

    def _aa_description(self):
        """
        A description of this site.
        """
        return

    def _aa_type(self):
        """
        The type of this site. Valid types include: DC, BU, AWS, and Office.
        """
        valid_site_types = ['dc', 'bu', 'office', 'aws']
        if self.value.lower() not in valid_site_types:
            raise ValidationError(
                "{0} not a valid site type".format(self.value)
            )
        if self.value.lower() == 'office':
            self.value = self.value.lower().title()
        else:
            self.value = self.value.upper()
