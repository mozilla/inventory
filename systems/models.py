from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.db.models.query import QuerySet
from django.contrib.auth.models import User

from dhcp.models import DHCP
from settings import BUG_URL
from mozdns.validation import validate_name

from core.validation import validate_mac
from core.site.models import Site
from core.keyvalue.mixins import KVUrlMixin
from core.keyvalue.models import KeyValue as BaseKeyValue
from core.mixins import CoreDisplayMixin

import datetime
import re
import socket


class QuerySetManager(models.Manager):
    def get_query_set(self):
        return self.model.QuerySet(self.model)

    def __getattr__(self, attr, *args):
        return getattr(self.get_query_set(), attr, *args)


class DirtyFieldsMixin(object):
    def __init__(self, *args, **kwargs):
        super(DirtyFieldsMixin, self).__init__(*args, **kwargs)
        post_save.connect(
            self._reset_state, sender=self.__class__,
            dispatch_uid='{0}-DirtyFieldsMixin-sweeper'.format(
                self.__class__.__name__)
        )
        self._reset_state()

    def _reset_state(self, *args, **kwargs):
        self._original_state = self._as_dict()

    def _as_dict(self):
        return dict([
            (f.attname, getattr(self, f.attname))
            for f in self._meta.local_fields
        ])

    def get_dirty_fields(self):
        new_state = self._as_dict()
        return dict([
            (key, value) for key, value
            in self._original_state.iteritems() if value != new_state[key]
        ])


class BuildManager(models.Manager):
    def get_query_set(self):
        return super(BuildManager, self).get_query_set().filter(
            allocation__name='release'
        )


class SystemWithRelatedManager(models.Manager):
    def get_query_set(self):
        objects = super(SystemWithRelatedManager, self).get_query_set()
        return objects.select_related(
            'operating_system',
            'server_model',
            'allocation',
            'system_rack',
        )


class Allocation(models.Model):
    name = models.CharField(max_length=255, blank=False)

    class Meta:
        db_table = u'allocations'
        ordering = ['name']

    def __unicode__(self):
        return self.name

    @classmethod
    def get_api_fields(cls):
        return ('name',)


class ScheduledTask(models.Model):
    task = models.CharField(max_length=255, blank=False, unique=True)
    type = models.CharField(max_length=255, blank=False)
    objects = QuerySetManager()

    class QuerySet(QuerySet):
        def delete_all_reverse_dns(self):
            self.filter(type='reverse_dns_zone').delete()

        def delete_all_dhcp(self):
            self.filter(type='dhcp').delete()

        def dns_tasks(self):
            return self.filter(type='dns')

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

    class Meta:
        db_table = u'locations'
        ordering = ['name']

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return '/systems/locations/show/{0}/'.format(self.pk)

    def get_edit_url(self):
        return self.get_absolute_url()


class PortData(models.Model):
    ip_address = models.CharField(max_length=15, blank=True)
    port = models.IntegerField(blank=True)
    protocol = models.CharField(max_length=3, blank=True)
    state = models.CharField(max_length=13, blank=True)
    service = models.CharField(max_length=64, blank=True)
    version = models.CharField(max_length=128, blank=True)

    def __unicode__(self):
        return self.ip_address

    class Meta:
        db_table = u'port_data'


class AdvisoryData(models.Model):
    ip_address = models.CharField(max_length=15, blank=True)
    advisory = models.TextField(blank=True)
    title = models.TextField(blank=True)
    severity = models.FloatField(blank=True)
    references = models.TextField(blank=True)

    class Meta:
        db_table = u'advisory_data'

    def __unicode__(self):
        return self.ip_address


class ApiManager(models.Manager):
    def get_query_set(self):
        results = super(ApiManager, self).get_query_set()
        return results


class KeyValue(BaseKeyValue, KVUrlMixin):
    obj = models.ForeignKey('System', null=True)
    objects = models.Manager()
    expanded_objects = ApiManager()

    class Meta:
        db_table = u'key_value'

    def __unicode__(self):
        return self.key if self.key else ''

    def __repr__(self):
        return "<{0}: '{1}'>".format(self.key, self.value)

    def save(self, *args, **kwargs):
        if re.match('^nic\.\d+\.mac_address\.\d+$', self.key):
            self.value = self.value.replace('-', ':')
            self.value = validate_mac(self.value)
        if self.key is None:
            self.key = ''
        if self.value is None:
            self.value = ''
        super(KeyValue, self).save(*args, **kwargs)


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

    class Meta:
        db_table = u'network_adapters'

    def save(self, *args, **kwargs):
        self.full_clean()  # Calls field.clean() on all fields.
        super(NetworkAdapter, self).save(*args, **kwargs)

    def get_system_host_name(self):
        systems = System.objects.filter(id=self.system_id)
        if systems:
            for system in systems:
                return system.hostname
        else:
            return ''


class Mac(models.Model):
    system = models.ForeignKey('System')
    mac = models.CharField(unique=True, max_length=17)

    class Meta:
        db_table = u'macs'


class OperatingSystem(models.Model):
    name = models.CharField(max_length=255, blank=True)
    version = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = u'operating_systems'
        ordering = ['name', 'version']

    def __unicode__(self):
        return "%s - %s" % (self.name, self.version)

    @classmethod
    def get_api_fields(cls):
        return ('name', 'version')


class ServerModel(models.Model):
    vendor = models.CharField(max_length=255, blank=True)
    model = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True, null=True)
    part_number = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = u'server_models'
        ordering = ['vendor', 'model']

    def __unicode__(self):
        return "%s - %s" % (self.vendor, self.model)

    @classmethod
    def get_api_fields(cls):
        return ('vendor', 'model', 'part_number', 'description')


class SystemRack(models.Model):
    name = models.CharField(max_length=255)
    site = models.ForeignKey(Site, null=True)
    location = models.ForeignKey('Location', null=True)

    search_fields = ('name', 'site__name')

    class Meta:
        db_table = u'system_racks'
        ordering = ['name']

    def __str__(self):
        return "%s - %s" % (
            self.name, self.site.full_name if self.site else ''
        )

    def __unicode__(self):
        return str(self)

    @classmethod
    def get_api_fields(cls):
        return ('name', 'location', 'site')

    def get_absolute_url(self):
        return '/en-US/systems/racks/?rack={0}'.format(self.pk)

    def get_edit_url(self):
        return '/en-US/systems/racks/edit/{0}/'.format(self.pk)

    def delete(self, *args, **kwargs):
        self.system_set.clear()
        super(SystemRack, self).delete(*args, **kwargs)

    def systems(self):
        return self.system_set.select_related().order_by('rack_order')


class SystemType(models.Model):
    type_name = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = u'system_types'

    def __unicode__(self):
        return self.type_name

    @classmethod
    def get_api_fields(cls):
        return ('type_name',)


class SystemStatus(models.Model):
    status = models.CharField(max_length=255, blank=True)
    color = models.CharField(max_length=255, blank=True)
    color_code = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = u'system_statuses'
        ordering = ['status']

    def __unicode__(self):
        return self.status

    @classmethod
    def get_api_fields(cls):
        return ('status',)


class System(DirtyFieldsMixin, CoreDisplayMixin, models.Model):

    YES_NO_CHOICES = (
        (0, 'No'),
        (1, 'Yes'),
    )

    # Related Objects
    operating_system = models.ForeignKey(
        'OperatingSystem', blank=True, null=True)
    server_model = models.ForeignKey('ServerModel', blank=True, null=True)
    allocation = models.ForeignKey('Allocation', blank=True, null=True)
    system_rack = models.ForeignKey('SystemRack', blank=True, null=True)
    system_type = models.ForeignKey('SystemType', blank=True, null=True)
    system_status = models.ForeignKey('SystemStatus', blank=True, null=True)

    hostname = models.CharField(
        unique=True, max_length=255, validators=[validate_name]
    )
    serial = models.CharField(max_length=255, blank=True, null=True)
    created_on = models.DateTimeField(null=True, blank=True)
    updated_on = models.DateTimeField(null=True, blank=True)
    oob_ip = models.CharField(max_length=30, blank=True, null=True)
    asset_tag = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    licenses = models.TextField(blank=True, null=True)
    rack_order = models.DecimalField(
        null=True, blank=True, max_digits=6, decimal_places=2)
    switch_ports = models.CharField(max_length=255, blank=True, null=True)
    patch_panel_port = models.CharField(max_length=255, blank=True, null=True)
    oob_switch_port = models.CharField(max_length=255, blank=True, null=True)
    purchase_date = models.DateField(null=True, blank=True)
    purchase_price = models.CharField(max_length=255, blank=True, null=True)
    change_password = models.DateTimeField(null=True, blank=True)
    ram = models.CharField(max_length=255, blank=True, null=True)
    is_dhcp_server = models.IntegerField(
        choices=YES_NO_CHOICES, blank=True, null=True)
    is_dns_server = models.IntegerField(
        choices=YES_NO_CHOICES, blank=True, null=True)
    is_puppet_server = models.IntegerField(
        choices=YES_NO_CHOICES, blank=True, null=True)
    is_nagios_server = models.IntegerField(
        choices=YES_NO_CHOICES, blank=True, null=True)
    is_switch = models.IntegerField(
        choices=YES_NO_CHOICES, blank=True, null=True)
    warranty_start = models.DateField(blank=True, null=True, default=None)
    warranty_end = models.DateField(blank=True, null=True, default=None)

    objects = models.Manager()
    build_objects = BuildManager()
    with_related = SystemWithRelatedManager()

    search_fields = (
        "hostname", "serial", "notes", "asset_tag",
        "oob_ip", "system_rack__site__full_name", "system_rack__name"
    )

    template = (
        "{hostname:$lhs_just} {oob_ip_str:$rdtype_just} INV "
        "{rdtype:$rdtype_just} {asset_tag_str} {serial_str}"
    )

    class Meta:
        db_table = u'systems'

    def __str__(self):
        return self.hostname

    @classmethod
    def get_api_fields(cls):
        return [
            'operating_system', 'server_model', 'allocation', 'system_rack',
            'system_type', 'system_status', 'hostname', 'serial', 'oob_ip',
            'asset_tag', 'notes', 'rack_order', 'switch_ports',
            'patch_panel_port', 'oob_switch_port', 'purchase_date',
            'purchase_price', 'change_password', 'warranty_start',
            'warranty_end',
        ]

    @property
    def primary_ip(self):
        try:
            first_ip = self.keyvalue_set.filter(
                key__contains='ipv4_address').order_by('key')[0].value
            return first_ip
        except:
            return None

    @property
    def primary_reverse(self):
        try:
            return str(socket.gethostbyaddr(self.primary_ip)[0])
        except:
            return None

    @property
    def notes_with_link(self):
        if not self.notes:
            return ''
        notes = self.notes
        pattern = '([bB]ug#?\D#?(\d+))'
        matches = re.findall(pattern, notes)
        for raw_text, bug_number in matches:
            bug_url = '<a href="{0}{1}">{2}</a>'.format(
                BUG_URL, bug_number, raw_text
            )
            notes = notes.replace(raw_text, bug_url, 1)
        return notes

    @classmethod
    def field_names(cls):
        return [field.name for field in cls._meta.fields]

    @classmethod
    def get_bulk_action_list(cls, query, fields=None, show_related=True):
        """
        Return a list of serialized system objects and their related objects to
        be used in the bulk_action api.

        This function will serialize and export StaticReg objects and their
        accompanying HWAdapter objects
        """
        if not fields:
            fields = cls.get_api_fields() + ['pk']

        # Pull in all system blobs and tally which pks we've seen. In one swoop
        # pull in all staticreg blobs and put them with their systems.
        sys_t_bundles = cls.objects.filter(query).values_list(*fields)

        sys_d_bundles = {}
        sys_pks = []
        for t_bundle in sys_t_bundles:
            d_bundle = dict(zip(fields, t_bundle))
            sys_d_bundles[d_bundle['pk']] = d_bundle
            if show_related:
                sys_pks.append(d_bundle['pk'])

        sys_q = Q(system__in=sys_pks)
        sreg_bundles = cls.staticreg_set.related.model.get_bulk_action_list(
            sys_q
        )

        hw_q = Q(sreg__system__in=sys_pks)
        hw_bundles = (
            cls.staticreg_set.related.model.
            hwadapter_set.related.model.get_bulk_action_list(hw_q)
        )

        # JOIN static_reg, hw_adapter ON sreg_pk
        for sreg_pk, hw_bundle in hw_bundles.iteritems():
            sreg_bundles[sreg_pk]['hwadapter_set'] = hw_bundle

        for sreg_pk, sreg_bundle in sreg_bundles.iteritems():
            sys_d_bundles[sreg_bundle['system']].setdefault(
                'static_reg_set', []
            ).append(sreg_bundle)

        return sys_d_bundles.values()

    @property
    def rdtype(self):
        return 'SYS'

    def bind_render_record(self, **kwargs):
        data = {
            'oob_ip_str': self.oob_ip or 'None',
            'asset_tag_str': self.asset_tag or 'None',
            'serial_str': self.serial or 'None'
        }
        return super(System, self).bind_render_record(**data)

    def save(self, *args, **kwargs):
        self.save_history(kwargs)
        self.full_clean()
        super(System, self).save(*args, **kwargs)

    def clean(self):
        self.validate_warranty()

    def validate_warranty(self):
        if bool(self.warranty_start) ^ bool(self.warranty_end):
            raise ValidationError(
                "Warranty must have a start and end date"
            )
        if not self.warranty_start:
            return
        if self.warranty_start.timetuple() > self.warranty_end.timetuple():
            raise ValidationError(
                "warranty start date should be before the end date"
            )

    def save_history(self, kwargs):
        request = kwargs.pop('request', None)
        try:
            changes = self.get_dirty_fields()
            if changes:
                system = System.objects.get(id=self.id)
                save_string = ''
                for k, v in changes.items():
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
                    save_string += '%s: %s\n\n' % (k, v)
                try:
                    remote_user = request.META['REMOTE_USER']
                except Exception:
                    remote_user = 'changed_user'
                tmp = SystemChangeLog(
                    system=system,
                    changed_by=remote_user,
                    changed_text=save_string,
                    changed_date=datetime.datetime.now()
                )
                tmp.save()
        except Exception:
            pass

        if not self.id:
            self.created_on = datetime.datetime.now()
        self.updated_on = datetime.datetime.now()

    def get_edit_url(self):
        return "/systems/edit/{0}/".format(self.pk)

    def get_absolute_url(self):
        return "/systems/show/{0}/".format(self.pk)

    def get_next_key_value_adapter(self):
        """
            Return the first found adapter from the
            key value store. This will go away,
            once we are on the StaticReg
            based system
        """
        ret = {}
        ret['mac_address'] = None
        ret['ip_address'] = None
        ret['num'] = None
        ret['dhcp_scope'] = None
        ret['name'] = 'nic0'
        key_value = self.keyvalue_set.filter(
            key__startswith='nic', key__icontains='mac_address')[0]
        m = re.search('nic\.(\d+)\.mac_address\.0', key_value.key)
        ret['num'] = int(m.group(1))
        key_value_set = self.keyvalue_set.filter(
            key__startswith='nic.%s' % ret['num'])
        if len(key_value_set) > 0:
            for kv in key_value_set:
                m = re.search('nic\.\d+\.(.*)\.0', kv.key)
                if m:
                    ret[m.group(1)] = str(kv.value)
            return ret
        else:
            return False

    def delete_key_value_adapter_by_index(self, index):
        """
            Delete a set of key_value items by index
            if index = 0
            delete where keyvalue.name startswith nic.0
        """
        self.keyvalue_set.filter(key__startswith='nic.%i' % index).delete()
        return True

    def get_updated_fqdn(self):
        allowed_domains = [
            'mozilla.com',
            'scl3.mozilla.com',
            'phx.mozilla.com',
            'phx1.mozilla.com',
            'mozilla.net',
            'mozilla.org',
            'build.mtv1.mozilla.com',
            'build.mozilla.org',
        ]
        reverse_fqdn = self.primary_reverse
        if self.primary_ip and reverse_fqdn:
            current_hostname = str(self.hostname)

            if current_hostname and current_hostname != reverse_fqdn:
                res = reverse_fqdn.replace(current_hostname, '').strip('.')
                if res in allowed_domains:
                    self.update_host_for_migration(reverse_fqdn)
        elif not self.primary_ip or self.primary_reverse:
            for domain in allowed_domains:
                updated = False
                if not updated:
                    try:
                        fqdn = socket.gethostbyaddr(
                            '%s.%s' % (self.hostname, domain)
                        )
                        if fqdn:
                            self.update_host_for_migration(fqdn[0])
                            updated = True
                    except Exception:
                        pass
            if not updated:
                pass
                #print "Could not update hostname %s" % (self.hostname)

    def update_host_for_migration(self, new_hostname):
        if new_hostname.startswith(self.hostname):
            kv = KeyValue(
                obj=self, key='system.hostname.alias.0', value=self.hostname
            )
            kv.save()
            try:
                self.hostname = new_hostname
                self.save()
            except Exception, e:
                print "ERROR - %s" % (e)

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
        pairs = KeyValue.objects.filter(
            obj=self, key__startswith='nic', key__contains='adapter_name'
        )
        for row in pairs:
            m = re.match('^nic\.\d+\.adapter_name\.\d+', row.key)
            if m:
                adapter_names.append(str(row.value))
        return adapter_names

    def get_adapter_numbers(self):
        nic_numbers = []
        pairs = KeyValue.objects.filter(obj=self, key__startswith='nic')
        for row in pairs:
            m = re.match('^nic\.(\d+)\.', row.key)
            if m:
                match = int(m.group(1))
                if match not in nic_numbers:
                    nic_numbers.append(match)
        return nic_numbers

    def get_adapter_count(self):
        return len(self.get_adapter_numbers())


class SystemChangeLog(models.Model):
    changed_by = models.CharField(max_length=255)
    changed_date = models.DateTimeField()
    changed_text = models.TextField()
    system = models.ForeignKey(System)

    class Meta:
        db_table = u'systems_change_log'


class UserProfile(models.Model):
    PAGER_CHOICES = (
        ('epager', 'epager'),
        ('sms', 'sms'),
    )
    user = models.ForeignKey(User, unique=True)

    is_desktop_oncall = models.BooleanField()
    is_sysadmin_oncall = models.BooleanField()
    is_services_oncall = models.BooleanField()
    is_mysqldba_oncall = models.BooleanField()
    is_pgsqldba_oncall = models.BooleanField()
    is_netop_oncall = models.BooleanField()

    current_desktop_oncall = models.BooleanField()
    current_sysadmin_oncall = models.BooleanField()
    current_services_oncall = models.BooleanField()
    current_mysqldba_oncall = models.BooleanField()
    current_pgsqldba_oncall = models.BooleanField()
    current_netop_oncall = models.BooleanField()

    irc_nick = models.CharField(max_length=128, null=True, blank=True)
    api_key = models.CharField(max_length=255, null=True, blank=True)
    pager_type = models.CharField(
        choices=PAGER_CHOICES, max_length=255, null=True, blank=True
    )
    pager_number = models.CharField(max_length=255, null=True, blank=True)
    epager_address = models.CharField(max_length=255, null=True, blank=True)
    objects = QuerySetManager()

    class Meta:
        db_table = u'user_profiles'

    def __str__(self):
        return "{0}".format(self.user.username)

    def __repr__(self):
        return "<UserProfile {0}>".format(self.user.username)

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
