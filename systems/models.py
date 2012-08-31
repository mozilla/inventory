# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#     * Rearrange models' order
#     * Make sure each model has one field with primary_key=True
# Feel free to rename the models, but don't rename db_table values or field names.
#
# Also note: You'll have to insert the output of 'django-admin.py sqlcustom [appname]'
# into your database.

from django.db import models
from django.core.exceptions import ValidationError

from dhcp.models import DHCP
from django.db.models.signals import post_save
from django.db.models.query import QuerySet
import datetime
import re
from django.contrib.auth.models import User
from settings import BUG_URL

import pdb

class QuerySetManager(models.Manager):
    def get_query_set(self):
        return self.model.QuerySet(self.model)
    def __getattr__(self, attr, *args):
        return getattr(self.get_query_set(), attr, *args)

class DirtyFieldsMixin(object):
    def __init__(self, *args, **kwargs):
        super(DirtyFieldsMixin, self).__init__(*args, **kwargs)
        post_save.connect(self._reset_state, sender=self.__class__,
                            dispatch_uid='%s-DirtyFieldsMixin-sweeper' % self.__class__.__name__)
        self._reset_state()

    def _reset_state(self, *args, **kwargs):
        self._original_state = self._as_dict()

    def _as_dict(self):
        return dict([(f.attname, getattr(self, f.attname)) for f in self._meta.local_fields])

    def get_dirty_fields(self):
        new_state = self._as_dict()
        return dict([(key, value) for key, value in self._original_state.iteritems() if value != new_state[key]])

class BuildManager(models.Manager):
    def get_query_set(self):
        return super(BuildManager, self).get_query_set().filter(allocation__name='release')

class SystemWithRelatedManager(models.Manager):
    def get_query_set(self):
        return super(SystemWithRelatedManager, self).get_query_set().select_related(
            'operating_system',
            'server_model',
            'allocation',
            'system_rack',
        )


class Allocation(models.Model):
    name = models.CharField(max_length=255, blank=False)

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = u'allocations'
        ordering = ['name']

class ScheduledTask(models.Model):
    task = models.CharField(max_length=255, blank=False, unique=True)
    type = models.CharField(max_length=255, blank=False)
    objects = QuerySetManager()
    class QuerySet(QuerySet):
        def delete_all_reverse_dns(self):
            self.filter(type='reverse_dns_zone').delete()
        def delete_all_dhcp(self):
            self.filter(type='dhcp').delete()
        def get_all_dhcp(self):
            return self.filter(type='dhcp')
        def get_all_reverse_dns(self):
            return self.filter(type='reverse_dns_zone')
        def get_next_task(self, type=None):
            if type is not None:
                try:
                    return self.filter(type=type)[0]
                except:
                    return None
            else:
                return None
        def get_last_task(self, type=None):
            if type is not None:
                try:
                    return self.filter(type=type)[-1]
                except:
                    return None
            else:
                return None
    class Meta:
        db_table = u'scheduled_tasks'
        ordering = ['task']

class Contract(models.Model):
    contract_number = models.CharField(max_length=255, blank=True)
    support_level = models.CharField(max_length=255, blank=True)
    contract_link = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=40, blank=True)
    expiration = models.DateTimeField(null=True, blank=True)
    system = models.ForeignKey('System')
    created_on = models.DateTimeField(null=True, blank=True)
    updated_on = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = u'contracts'

class Location(models.Model):
    name = models.CharField(unique=True, max_length=255, blank=True)
    address = models.TextField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = u'locations'
        ordering = ['name']
class ApiManager(models.Manager):
    def get_query_set(self):
        results = super(ApiManager, self).get_query_set()
        return results

class KeyValue(models.Model):
    system = models.ForeignKey('System')
    key = models.CharField(max_length=255, blank=True, null=True)
    value = models.CharField(max_length=255, blank=True, null=True)
    objects = models.Manager()
    expanded_objects = ApiManager()

    def __unicode__(self):
        return self.key if self.key else ''

    def __repr__(self):
        return self.key if self.key else ''
    def save(self, *args, **kwargs):
        if re.match('^nic\.\d+\.mac_address\.\d+$', self.key):
            self.value = validate_mac(self.value)
        super(KeyValue, self).save(*args, **kwargs)


    class Meta:
        db_table = u'key_value'

# Eventually, should this go in the KV class? Depends on whether other code
# calls this.
def validate_mac(mac):
    """
    Validates a mac address. If the mac is in the form XX-XX-XX-XX-XX-XX this
    function will replace all '-' with ':'.

    :param mac: The mac address
    :type mac: str
    :returns: The valid mac address.
    :raises: ValidationError
    """
    mac = mac.replace('-',':')
    if not re.match('^([0-9a-fA-F]{2}(:|$)){6}$', mac):
        raise ValidationError("Please enter a valid Mac Address in the form "
                                "XX:XX:XX:XX:XX:XX")
    return mac

class NetworkAdapter(models.Model):
    system_id = models.IntegerField()
    mac_address = models.CharField(max_length=255)
    ip_address = models.CharField(max_length=255)
    adapter_name = models.CharField(max_length=255)
    system_id = models.CharField(max_length=255)
    switch_port = models.CharField(max_length=128)
    filename = models.CharField(max_length=64)
    option_host_name = models.CharField(max_length=64)
    option_domain_name = models.CharField(max_length=128)
    dhcp_scope = models.ForeignKey(DHCP, null=True, blank=True)
    switch_id = models.IntegerField(null=True, blank=True)

    def save(self, *args, **kwargs):
        self.full_clean() # Calls field.clean() on all fields.
        super(NetworkAdapter, self).save(*args, **kwargs)

    def get_system_host_name(self):
        systems = System.objects.filter(id=self.system_id)
        if systems:
            for system in systems:
                return system.hostname
        else:
            return ''
    class Meta:
        db_table = u'network_adapters'

class Mac(models.Model):
    system = models.ForeignKey('System')
    mac = models.CharField(unique=True, max_length=17)
    class Meta:
        db_table = u'macs'

class OperatingSystem(models.Model):
    name = models.CharField(max_length=255, blank=True)
    version = models.CharField(max_length=255, blank=True)

    def __unicode__(self):
        return "%s - %s" % (self.name, self.version)

    class Meta:
        db_table = u'operating_systems'
        ordering = ['name', 'version']

class ServerModel(models.Model):
    vendor = models.CharField(max_length=255, blank=True)
    model = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True, null=True)
    part_number = models.CharField(max_length=255, blank=True, null=True)

    def __unicode__(self):
        return "%s - %s" % (self.vendor, self.model)

    class Meta:
        db_table = u'server_models'
        ordering = ['vendor', 'model']

class SystemRack(models.Model):
    name = models.CharField(max_length=255, blank=True)
    location = models.ForeignKey('Location')

    def __unicode__(self):
        return "%s - %s" % (self.name, self.location.name)

    def delete(self, *args, **kwargs):
        self.system_set.clear()
        super(SystemRack, self).delete(*args, **kwargs)

    def systems(self):
        return self.system_set.select_related().order_by('rack_order')

    class Meta:
        db_table = u'system_racks'
        ordering = ['name']


class SystemType(models.Model):
    type_name = models.CharField(max_length=255, blank=True)

    def __unicode__(self):
        return self.type_name

    class Meta:
        db_table = u'system_types'

class SystemStatus(models.Model):
    status = models.CharField(max_length=255, blank=True)
    color = models.CharField(max_length=255, blank=True)
    color_code = models.CharField(max_length=255, blank=True)
    def __unicode__(self):
        return self.status

    class Meta:
        db_table = u'system_statuses'
        ordering = ['status']



class System(DirtyFieldsMixin, models.Model):

    YES_NO_CHOICES = (
    (0, 'No'),
    (1, 'Yes'),
    )
    hostname = models.CharField(unique=True, max_length=255)
    serial = models.CharField(max_length=255, blank=True, null=True)
    operating_system = models.ForeignKey('OperatingSystem', blank=True, null=True)
    server_model = models.ForeignKey('ServerModel', blank=True, null=True)
    created_on = models.DateTimeField(null=True, blank=True)
    updated_on = models.DateTimeField(null=True, blank=True)
    oob_ip = models.CharField(max_length=30, blank=True, null=True)
    asset_tag = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    licenses = models.TextField(blank=True, null=True)
    allocation = models.ForeignKey('Allocation', blank=True, null=True)
    system_rack = models.ForeignKey('SystemRack', blank=True, null=True)
    rack_order = models.DecimalField(null=True, blank=True, max_digits=6, decimal_places=2)
    switch_ports = models.CharField(max_length=255, blank=True, null=True)
    patch_panel_port = models.CharField(max_length=255, blank=True, null=True)
    oob_switch_port = models.CharField(max_length=255, blank=True, null=True)
    purchase_date = models.DateField(null=True, blank=True)
    purchase_price = models.CharField(max_length=255, blank=True, null=True)
    system_status = models.ForeignKey('SystemStatus', blank=True, null=True)
    change_password = models.DateTimeField(null=True, blank=True)
    ram = models.CharField(max_length=255, blank=True, null=True)
    is_dhcp_server = models.IntegerField(choices=YES_NO_CHOICES, blank=True, null=True)
    is_dns_server = models.IntegerField(choices=YES_NO_CHOICES, blank=True, null=True)
    is_puppet_server = models.IntegerField(choices=YES_NO_CHOICES, blank=True, null=True)
    is_nagios_server = models.IntegerField(choices=YES_NO_CHOICES, blank=True, null=True)
    is_switch = models.IntegerField(choices=YES_NO_CHOICES, blank=True, null=True)
    #network_adapter = models.ForeignKey('NetworkAdapter', blank=True, null=True)




    objects = models.Manager()
    build_objects = BuildManager()
    with_related = SystemWithRelatedManager()

    def save(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        try:
            changes = self.get_dirty_fields()
            if changes:
                system = System.objects.get(id=self.id)
                save_string = ''
                for k,v in changes.items():
                    if k == 'system_status_id':
                        k = 'System Status'
                        ss = SystemStatus.objects.get(id=v)
                        v = ss
                    if k == 'operating_system_id':
                        k = 'Operating System'
                        ss = OperatingSystem.objects.get(id=v)
                        v = ss
                    if k == 'server_model_id':
                        k = 'Server Model'
                        ss = ServerModel.objects.get(id=v)
                        v = ss
                    save_string += '%s: %s\n\n' % (k,v)
                try:
                    remote_user = request.META['REMOTE_USER']
                except Exception, e:
                    remote_user = 'changed_user'
                tmp = SystemChangeLog(system=system,changed_by = remote_user,changed_text = save_string, changed_date = datetime.datetime.now())
                tmp.save()
        except Exception, e:
            print e
            pass

        if not self.id:
            self.created_on = datetime.datetime.now()
        self.updated_on = datetime.datetime.now()

        super(System, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.hostname
    def get_switches(self):
        return System.objects.filter(is_switch=1)

    def check_for_adapter(self, adapter_id):
        adapter_id = int(adapter_id)
        if adapter_id in self.get_adapter_numbers():
            return True
        return False

    def check_for_adapter_name(self, adapter_name):
        adapter_name = str(adapter_name)
        if adapter_name in self.get_nic_names():
            return True
        return False

    def get_nic_names(self):
        adapter_names = []
        pairs = KeyValue.objects.filter(system=self,key__startswith='nic', key__contains='adapter_name')
        for row in pairs:
            m = re.match('^nic\.\d+\.adapter_name\.\d+', row.key)
            if m:
                adapter_names.append(str(row.value))
        return adapter_names
    def get_adapter_numbers(self):
        nic_numbers = []
        pairs = KeyValue.objects.filter(system=self,key__startswith='nic')
        for row in pairs:
            m = re.match('^nic\.(\d+)\.', row.key)
            if m:
                match = int(m.group(1))
                if match not in nic_numbers:
                    nic_numbers.append(match)
        return nic_numbers

    @property
    def notes_with_link(self):
        if self.notes:
            patterns = [
                '[bB]ug#?\D#?(\d+)',
                    ]
            for pattern in patterns:
                m = re.search(pattern, self.notes)
                if m:
                    self.notes = re.sub(pattern, '<a href="%s%s">Bug %s</a>' % (BUG_URL, m.group(1), m.group(1)), self.notes)
            return self.notes
        else:
            return ''
    def get_next_adapter_number(self):
        nic_numbers = self.get_adapter_numbers()
        if len(nic_numbers) > 0:
            nic_numbers.sort()
            ## The last item in the array should be an int, but just in case we'll catch the exception and return a 1
            try:
                return nic_numbers[-1] + 1
            except:
                return 1
        else:
            return 1

    def get_adapter_count(self):
        return len(self.get_adapter_numbers())

    class Meta:
        db_table = u'systems'

class SystemChangeLog(models.Model):
    changed_by = models.CharField(max_length=255)
    changed_date = models.DateTimeField()
    changed_text = models.TextField()
    system = models.ForeignKey(System)
    class Meta:
        db_table = u'systems_change_log'
#class UserProfile(models.Model):
#    api_key = models.CharField(max_length=255, blank=True, null=True)
#    user = models.ForeignKey(User, unique=True)
#    class Meta:
##        db_table = u'user_profiles'
class UserProfile(models.Model):
    PAGER_CHOICES = (
            ('epager', 'epager'),
            ('sms', 'sms'),
    )
    user = models.ForeignKey(User, unique=True)
    is_desktop_oncall = models.BooleanField()
    is_sysadmin_oncall = models.BooleanField()
    is_services_oncall = models.BooleanField()
    current_desktop_oncall = models.BooleanField()
    current_sysadmin_oncall = models.BooleanField()
    current_services_oncall = models.BooleanField()
    irc_nick = models.CharField(max_length=128, null=True, blank=True)
    api_key = models.CharField(max_length=255, null=True, blank=True)
    pager_type = models.CharField(choices=PAGER_CHOICES, max_length=255, null=True, blank=True)
    pager_number = models.CharField(max_length=255, null=True, blank=True)
    epager_address = models.CharField(max_length=255, null=True, blank=True)
    objects = QuerySetManager()
    class QuerySet(QuerySet):
        def get_all_desktop_oncall(self):
            self.filter(is_desktop_oncall=1)
        def get_current_desktop_oncall(self):
            self.filter(current_desktop_oncall=1).select_related()

        def get_all_services_oncall(self):
            self.filter(is_services_oncall=1)
        def get_current_services_oncall(self):
            self.filter(current_services_oncall=1).select_related()

        def get_all_sysadmin_oncall(self):
            self.filter(is_sysadmin_oncall=1)
        def get_current_sysadmin_oncall(self):
            self.filter(current_sysadmin_oncall=1).select_related()

    class Meta:
        db_table = u'user_profiles'

