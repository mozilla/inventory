from django.db import models

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
