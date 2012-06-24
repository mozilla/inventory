from django.db import models
from django.core.exceptions import ValidationError

from core.site.models import Site
from core.mixins import ObjectUrlMixin

class Vlan(models.Model, ObjectUrlMixin):
    id = models.AutoField(primary_key=True)
    site = models.ForeignKey(Site, null=True, blank=True)
    vlan_name = models.CharField(max_length=255)
    vlan_number = models.PositiveIntegerField()

    def details(self):
        return (
                ('Name', self.vlan_name),
                ('Number', self.vlan_number),
                )
    class Meta:
        db_table = 'vlan'
        unique_together = ('vlan_name', 'vlan_number')

    def __str__(self):
        return "{0} {0}".format(self.vlan_name, self.vlan_number)

    def __repr__(self):
        return "<Vlan {0}>".format(str(self))
