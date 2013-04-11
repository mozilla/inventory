from django.db import models
from django.contrib.auth.models import User

from datetime import datetime


class OncallAssignment(models.Model):
    user = models.ForeignKey(User)
    oncall_type = models.CharField(max_length=128, blank=True)

    class Meta:
        db_table = 'oncall_assignment'
        ordering = ['oncall_type']

    def __str__(self):
        return "%s - %s" % (self.oncall_type, self.user)

    def __unicode__(self):
        return unicode(str(self))  # ??

    def save(self, *args, **kwargs):
        t = OncallTimestamp.objects.get_or_create(
            oncall_type=self.oncall_type
        )[0]
        t.updated_on = datetime.now()
        t.save()
        super(OncallAssignment, self).save(*args, **kwargs)

    @property
    def updated_on(self):
        return OncallTimestamp.objects.get_or_create(
            oncall_type=self.oncall_type
        )[0].updated_on


class OncallTimestamp(models.Model):
    updated_on = models.DateTimeField(
        null=False, blank=False, default=datetime.now()
    )
    oncall_type = models.CharField(max_length=128, null=False, blank=False)

    class Meta:
        db_table = 'oncall_timestamp'

    def __str__(self):
        return "%s %s" % (self.oncall_type, self.updated_on)

    def __repr__(self):
        return '<OncallTimestamp %s>' % self
