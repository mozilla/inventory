from django.db import models
from systems.models import System

# Create your models here.

class BuildPurpose(models.Model):
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name

class BuildAttribute(models.Model):

    TIER_CHOICES = (
        ('Tier 1', 'Tier 1'),
        ('Tier 2', 'Tier 2'),
        ('Tier 3', 'Tier 3'),
    )
    support_tier = models.CharField(max_length=255, blank=True, choices=TIER_CHOICES)
    purposes = models.ManyToManyField('BuildPurpose', db_table='build_attributes_purposes', blank=True)
    system = models.OneToOneField(System)
    tboxtree_url = models.CharField(max_length=255, blank=True)
    cvsbranch = models.CharField(max_length=255, blank=True)
    cpu_throttled = models.BooleanField(blank=True)
    product_branch = models.CharField(max_length=255, blank=True)
    closes_tree = models.BooleanField(blank=True)
    support_doc = models.CharField(max_length=255, blank=True)
    pool_name = models.CharField(max_length=255, blank=True)
    product_series = models.CharField(max_length=255, blank=True)
    class Meta:
        db_table = u'build_attributes'
