from django.db import models
from systems.models import OperatingSystem, ServerModel
from datetime import datetime, timedelta, date
from django.db.models.query import QuerySet
from settings.local import USER_SYSTEM_ALLOWED_DELETE, FROM_EMAIL_ADDRESS, UNAUTHORIZED_EMAIL_ADDRESS, BUG_URL
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail

# Create your models here.
YES_NO_CHOICES = (
        (0, 'No'),
        (1, 'Yes'),
    )


OS_CHOICES = (
	(1, 'Mac OS'),
	(2, 'Windows'),
	)



class QuerySetManager(models.Manager):
    def get_query_set(self):
        return self.model.QuerySet(self.model)
    def __getattr__(self, attr, *args):
        return getattr(self.get_query_set(), attr, *args)
class UserOperatingSystem(models.Model):
    name = models.CharField(max_length=128, blank=False)
    def __unicode__(self):
        return self.name
    
class UnmanagedSystemType(models.Model):
    name = models.CharField(max_length=128, blank=False)
    def __unicode__(self):
        return self.name
    class Meta:
        db_table = 'unmanaged_system_types'


class CostCenter(models.Model):
    cost_center_number = models.IntegerField()
    name = models.CharField(max_length=255, blank=True)

    def __unicode__(self):
        return '%s - %s' % (self.cost_center_number, self.name)

    class Meta:
        db_table = 'cost_centers'

class UnmanagedSystem(models.Model):
    serial = models.CharField(max_length=255, blank=True)
    asset_tag = models.CharField(max_length=255, blank=True)
    operating_system = models.ForeignKey(OperatingSystem, blank=True, null=True)
    owner = models.ForeignKey('Owner', blank=True, null=True)
    system_type = models.ForeignKey('UnmanagedSystemType', blank=True, null=True)
    server_model = models.ForeignKey(ServerModel, blank=True, null=True)
    created_on = models.DateTimeField(null=True, blank=True)
    updated_on = models.DateTimeField(null=True, blank=True)
    date_purchased = models.DateField(null=True, blank=True)
    cost = models.CharField(max_length=50, blank=True)
    cost_center = models.ForeignKey('CostCenter', null=True, blank=True)
    bug_number = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    is_loaned = models.IntegerField(choices=YES_NO_CHOICES, blank=True, null=True)
    is_loaner = models.IntegerField(choices=YES_NO_CHOICES, blank=True, null=True)
    loaner_return_date = models.DateTimeField(null=True, blank=True)
    objects = QuerySetManager()

    search_fields = (
            'serial', 
            'asset_tag',
            'owner__name',
            'server_model__vendor',
            'notes',
            'server_model__model'
        )

    def delete(self, *args, **kwargs):
        super(UnmanagedSystem, self).delete(*args, **kwargs)

    def save(self):
        if not self.id:
            self.created_on = datetime.now()
        self.updated_on = datetime.now()
        super(UnmanagedSystem, self).save()

    def __unicode__(self):
        try:
            server_model = self.server_model
        except ServerModel.DoesNotExist:
            server_model = ""
        return "%s - %s - %s" % (server_model, self.asset_tag, self.serial) 

    class QuerySet(QuerySet):
        def get_all_loaners(self):
            return self.filter(is_loaner=1)

        def get_loaners_due(self):
            return_date = date.today()
            return self.filter(loaner_return_date__lte=return_date)

    def get_bug_url(self):
        bug_id = ''
        if self.bug_number:
            bug_id = self.bug_number
        return "%s%s" % (BUG_URL, bug_id)

    @models.permalink
    def get_absolute_url(self):
        return ('user-system-show', [self.id])

    class Meta:
        db_table = u'unmanaged_systems'

class History(models.Model):
    change = models.CharField(max_length=1000)
    changed_by = models.CharField(max_length=128, null=True, blank=True)
    system = models.ForeignKey(UnmanagedSystem)
    created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        "%s: %s" % (self.created, self.change)

    class Meta:
        ordering = ['-created']

class Owner(models.Model):
    name = models.CharField(unique=True, max_length=255, blank=True)
    address = models.TextField(blank=True)
    note = models.TextField(blank=True)
    user_location = models.ForeignKey('UserLocation', blank=True, null=True)
    email = models.CharField(max_length=255, blank=True)

    search_fields = (
            'name',
            'note',
            'email',
            )

    def __unicode__(self):
        return self.name

    def upgradeable_systems(self):
        return self.unmanagedsystem_set.filter(
            date_purchased__lt=datetime.now() - timedelta(days=730))

    @models.permalink
    def get_absolute_url(self):
        return ('owner-show', [self.id])

    def delete(self):
        UserLicense.objects.filter(owner=self).update(owner=None)
        UnmanagedSystem.objects.filter(owner=self).update(owner=None)
        super(Owner, self).delete()

    class Meta:
        db_table = u'owners'
        ordering = ['name']

class UserLicense(models.Model):
    username = models.CharField(max_length=255, blank=True)
    version = models.CharField(max_length=255, blank=True)
    license_type = models.CharField(max_length=255, blank=True)
    license_key = models.CharField(max_length=255, blank=False)
    owner = models.ForeignKey('Owner', blank=True, null=True)
    #user_operating_system = models.IntegerField(choices=OS_CHOICES, blank=True, null=True)
    user_operating_system = models.ForeignKey('UserOperatingSystem', blank=True, null=True)
    search_fields = (
            'username', 
            'version',
            'license_type',
            'license_key',
            'owner__name',
            'user_operating_system__name',
	)
    def delete(self, *args, **kwargs):
        super(UserLicense, self).delete(*args, **kwargs)

    def __unicode__(self):
        return "%s - %s" % (self.license_type, self.license_key)

    @models.permalink
    def get_absolute_url(self):
        return ('license-show', [self.id])

    class Meta:
        db_table = u'user_licenses'
        ordering = ['license_type']

class UserLocation(models.Model):
    city = models.CharField(unique=True, max_length=255, blank=True)
    country = models.CharField(unique=True, max_length=255, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    def __unicode__(self):
        return "%s - %s" % (self.city, self.country)

    class Meta:
        db_table = u'user_locations'
