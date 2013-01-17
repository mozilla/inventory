from django.db import models

from mozdns.mixins import ObjectUrlMixin


class View(models.Model, ObjectUrlMixin):
    """
    >>> View(name=name)
    """

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)

    def details(self):
        return (
            ('Name', self.name),
        )

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<View: {0}>".format(self)

    class Meta:
        db_table = 'view'
        unique_together = ('name',)
