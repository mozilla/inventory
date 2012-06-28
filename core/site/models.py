from django.db import models
from django.core.exceptions import ValidationError

from core.mixins import ObjectUrlMixin
from core.keyvalue.models import KeyValue


class Site(models.Model, ObjectUrlMixin):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    parent = models.ForeignKey("self", null=True, blank=True)

    def details(self):
        return (
                ('Name', self.get_full_name()),
                )

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


    class Meta:
        db_table = 'site'
        unique_together = ('name','parent')

    def __str__(self):
        return "{0}".format(self.get_full_name())

    def __repr__(self):
        return "<Site {0}>".format(str(self))

class SiteKeyValue(KeyValue):
    site = models.ForeignKey(Site, null=False)
    aux_attrs = (
        ('address','A site\'s address'),
        ('description', 'A description of the site')
        )
    class Meta:
        db_table = 'site_key_value'
        unique_together = ('key', 'value')

    def address(self):
        # Everything is valid
        return

    def description(self):
        return
