from django.db import models
from systems.models import ScheduledTask
from django.db import IntegrityError
import pdb

# Create your models here.

class Truth(models.Model):
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=128)

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = u'truth'

class ApiManager(models.Manager):
	def get_query_set(self):
		results = super(ApiManager, self).get_query_set()
		return results

class KeyValue(models.Model):
    truth = models.ForeignKey('Truth')
    key = models.CharField(max_length=255, blank=True, null=True)
    value = models.CharField(max_length=255, blank=True, null=True)
    objects = models.Manager()
    expanded_objects = ApiManager()

    def __unicode__(self):
        return self.key

    class Meta:
        db_table = u'truth_key_value'

    def save(self, *args, **kwargs):
        if self.truth.name == "ip_to_vlan_mapping":
            try:
                ScheduledTask(type='dns', task=self.key).save()
            except IntegrityError, e:
                print ("Key {0} and Value {1} already existsed in "
                    "table".format(self.key, self.value))
        super(KeyValue, self).save(*args, **kwargs)
