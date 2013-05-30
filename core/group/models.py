from django.db import models

from core.mixins import ObjectUrlMixin

from core.keyvalue.base_option import DHCPKeyValue, CommonOption


class Group(models.Model, ObjectUrlMixin):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    #parent_group = models.ForeignKey('Group', null=True, blank=True)

    def details(self):
        return (
            ("Name", self.name),
        )

    class Meta:
        db_table = "group"
        unique_together = ("name",)

    def __str__(self):
        return "{0}".format(self.name)

    def __repr__(self):
        return "<Group: {0}>".format(self)

    @classmethod
    def get_api_fields(cls):
        return ['name']


class GroupKeyValue(DHCPKeyValue, CommonOption):
    obj = models.ForeignKey(Group, related_name='keyvalue_set', null=False)

    class Meta:
        db_table = "group_key_value"
        unique_together = ("key", "value")

    def _aa_description(self):
        return
