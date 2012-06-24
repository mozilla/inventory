from django.db import models
from django.core.exceptions import ValidationError

from core.mixins import ObjectUrlMixin

class Site(models.Model, ObjectUrlMixin):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)


    def details(self):
        return (
                ('Name', self.name),
                )

    class Meta:
        db_table = 'site'
        unique_together = ('name',)

    def __str__(self):
        return "{0}".format(self.name)

    def __repr__(self):
        return "<Site {0}>".format(str(self))
