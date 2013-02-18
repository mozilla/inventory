from django.db import models
from django.core.exceptions import ValidationError

from core.mixins import ObjectUrlMixin
from core.keyvalue.models import KeyValue
from core.utils import networks_to_Q, to_a


class Site(models.Model, ObjectUrlMixin):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    parent = models.ForeignKey("self", null=True, blank=True)

    def details(self):
        details = [
            ('Name', self.full_name),
        ]
        if self.parent:
            details.append(
                ('Parent Site', to_a(self.parent.full_name, self.parent))
            )
        return details

    @property
    def full_name(self):
        return self.get_full_name()

    def get_full_name(self):
        full_name = self.name
        target = self
        while True:
            if target.parent is None:
                break
            else:
                full_name = target.parent.name + " " + target.name
                target = target.parent
        return full_name.title()

    def get_site_path(self):
        full_name = self.name
        target = self
        while True:
            if target.parent is None:
                break
            else:
                full_name = target.name + '.' + target.parent.name
                target = target.parent
        return full_name

    def compile_Q(self):
        """Compile a Django Q that will match any IP inside this site."""
        return networks_to_Q(self.network_set.all())

    class Meta:
        db_table = 'site'
        unique_together = ('name', 'parent')

    def __str__(self):
        return "{0}".format(self.get_full_name())

    def __repr__(self):
        return "<Site {0}>".format(str(self))


class SiteKeyValue(KeyValue):
    obj = models.ForeignKey(Site, related_name='keyvalue_set', null=False)

    class Meta:
        db_table = 'site_key_value'
        unique_together = ('key', 'value')

    def _aa_address(self):
        # Everything is valid
        return

    def _aa_description(self):
        return

    def _aa_type(self):
        """
        The type of this site. Valid types include: DC, BU and Office.
        """
        valid_site_types = ['dc', 'bu', 'office']
        if self.value.lower() not in valid_site_types:
            raise ValidationError(
                "{0} not a valid site type".format(self.value)
            )
        if self.value.lower() == 'office':
            self.value = self.value.lower().title()
        else:
            self.value = self.value.upper()
