from django.db import models
from django.core.exceptions import ValidationError

from core.site.models import Site
from core.mixins import ObjectUrlMixin

from core.keyvalue.models import KeyValue


class Vlan(models.Model, ObjectUrlMixin):
    id = models.AutoField(primary_key=True)
    #site = models.ForeignKey(Site, null=True, blank=True)
    name = models.CharField(max_length=255)
    number = models.PositiveIntegerField()

    def details(self):
        return (
                ('Name', self.name),
                ('Number', self.number),
                )

    class Meta:
        db_table = 'vlan'
        unique_together = ('name', 'number')

    def __str__(self):
        return "{0} {1}".format(self.name, self.number)

    def __repr__(self):
        return "<Vlan {0}>".format(str(self))

class VlanKeyValue(KeyValue):
    vlan = models.ForeignKey(Vlan, null=False)
    aux_attrs = (
        ('description', 'A description of the site'),
        ('router_label', 'In some instances the label on the \n'
            '\t\t\t\tnetworking equipment differs from the DNS label.  This is that\n'
            '\t\t\t\tlabel and is relevant to Netops mostly.\n'),
        ('dns_name', 'label within he FWDN up to the site label.\n'
            '\t\t\t\tBy default this is assumed to be the vlan name.\n'),
        )
    class Meta:
        db_table = 'vlan_key_value'
        unique_together = ('key', 'value')

    def description(self):
        return
