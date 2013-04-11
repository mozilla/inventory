# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Allocation'
        db.create_table(u'allocations', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('systems', ['Allocation'])

        # Adding model 'ScheduledTask'
        db.create_table(u'scheduled_tasks', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('task', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('systems', ['ScheduledTask'])

        # Adding model 'Contract'
        db.create_table(u'contracts', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('contract_number', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('support_level', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('contract_link', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('phone', self.gf('django.db.models.fields.CharField')(max_length=40, blank=True)),
            ('expiration', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('system', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['systems.System'])),
            ('created_on', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('updated_on', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal('systems', ['Contract'])

        # Adding model 'Location'
        db.create_table(u'locations', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255, blank=True)),
            ('address', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('note', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('systems', ['Location'])

        # Adding model 'PortData'
        db.create_table(u'port_data', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ip_address', self.gf('django.db.models.fields.CharField')(max_length=15, blank=True)),
            ('port', self.gf('django.db.models.fields.IntegerField')(blank=True)),
            ('protocol', self.gf('django.db.models.fields.CharField')(max_length=3, blank=True)),
            ('state', self.gf('django.db.models.fields.CharField')(max_length=13, blank=True)),
            ('service', self.gf('django.db.models.fields.CharField')(max_length=64, blank=True)),
            ('version', self.gf('django.db.models.fields.CharField')(max_length=128, blank=True)),
        ))
        db.send_create_signal('systems', ['PortData'])

        # Adding model 'AdvisoryData'
        db.create_table(u'advisory_data', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ip_address', self.gf('django.db.models.fields.CharField')(max_length=15, blank=True)),
            ('advisory', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('title', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('severity', self.gf('django.db.models.fields.FloatField')(blank=True)),
            ('references', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('systems', ['AdvisoryData'])

        # Adding model 'KeyValue'
        db.create_table(u'key_value', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('system', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['systems.System'])),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
        ))
        db.send_create_signal('systems', ['KeyValue'])

        # Adding model 'NetworkAdapter'
        db.create_table(u'network_adapters', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('mac_address', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('ip_address', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('adapter_name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('system_id', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('switch_port', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('filename', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('option_host_name', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('option_domain_name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('dhcp_scope', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dhcp.DHCP'], null=True, blank=True)),
            ('switch_id', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('systems', ['NetworkAdapter'])

        # Adding model 'Mac'
        db.create_table(u'macs', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('system', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['systems.System'])),
            ('mac', self.gf('django.db.models.fields.CharField')(unique=True, max_length=17)),
        ))
        db.send_create_signal('systems', ['Mac'])

        # Adding model 'OperatingSystem'
        db.create_table(u'operating_systems', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('version', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
        ))
        db.send_create_signal('systems', ['OperatingSystem'])

        # Adding model 'ServerModel'
        db.create_table(u'server_models', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('vendor', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('model', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('part_number', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
        ))
        db.send_create_signal('systems', ['ServerModel'])

        # Adding model 'SystemRack'
        db.create_table(u'system_racks', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('location', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['systems.Location'])),
        ))
        db.send_create_signal('systems', ['SystemRack'])

        # Adding model 'SystemType'
        db.create_table(u'system_types', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('type_name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
        ))
        db.send_create_signal('systems', ['SystemType'])

        # Adding model 'SystemStatus'
        db.create_table(u'system_statuses', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('color', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('color_code', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
        ))
        db.send_create_signal('systems', ['SystemStatus'])

        # Adding model 'System'
        db.create_table(u'systems', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('hostname', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('serial', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('operating_system', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['systems.OperatingSystem'], null=True, blank=True)),
            ('server_model', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['systems.ServerModel'], null=True, blank=True)),
            ('created_on', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('updated_on', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('oob_ip', self.gf('django.db.models.fields.CharField')(max_length=30, null=True, blank=True)),
            ('asset_tag', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('notes', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('licenses', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('allocation', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['systems.Allocation'], null=True, blank=True)),
            ('system_rack', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['systems.SystemRack'], null=True, blank=True)),
            ('rack_order', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=6, decimal_places=2, blank=True)),
            ('switch_ports', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('patch_panel_port', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('oob_switch_port', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('purchase_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('purchase_price', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('system_status', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['systems.SystemStatus'], null=True, blank=True)),
            ('change_password', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('ram', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('is_dhcp_server', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('is_dns_server', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('is_puppet_server', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('is_nagios_server', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('is_switch', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('systems', ['System'])

        # Adding model 'SystemChangeLog'
        db.create_table(u'systems_change_log', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('changed_by', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('changed_date', self.gf('django.db.models.fields.DateTimeField')()),
            ('changed_text', self.gf('django.db.models.fields.TextField')()),
            ('system', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['systems.System'])),
        ))
        db.send_create_signal('systems', ['SystemChangeLog'])

        # Adding model 'UserProfile'
        db.create_table(u'user_profiles', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], unique=True)),
            ('is_desktop_oncall', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_sysadmin_oncall', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_services_oncall', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('current_desktop_oncall', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('current_sysadmin_oncall', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('current_services_oncall', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('irc_nick', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
            ('api_key', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('pager_type', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('pager_number', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('epager_address', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
        ))
        db.send_create_signal('systems', ['UserProfile'])


    def backwards(self, orm):
        # Deleting model 'Allocation'
        db.delete_table(u'allocations')

        # Deleting model 'ScheduledTask'
        db.delete_table(u'scheduled_tasks')

        # Deleting model 'Contract'
        db.delete_table(u'contracts')

        # Deleting model 'Location'
        db.delete_table(u'locations')

        # Deleting model 'PortData'
        db.delete_table(u'port_data')

        # Deleting model 'AdvisoryData'
        db.delete_table(u'advisory_data')

        # Deleting model 'KeyValue'
        db.delete_table(u'key_value')

        # Deleting model 'NetworkAdapter'
        db.delete_table(u'network_adapters')

        # Deleting model 'Mac'
        db.delete_table(u'macs')

        # Deleting model 'OperatingSystem'
        db.delete_table(u'operating_systems')

        # Deleting model 'ServerModel'
        db.delete_table(u'server_models')

        # Deleting model 'SystemRack'
        db.delete_table(u'system_racks')

        # Deleting model 'SystemType'
        db.delete_table(u'system_types')

        # Deleting model 'SystemStatus'
        db.delete_table(u'system_statuses')

        # Deleting model 'System'
        db.delete_table(u'systems')

        # Deleting model 'SystemChangeLog'
        db.delete_table(u'systems_change_log')

        # Deleting model 'UserProfile'
        db.delete_table(u'user_profiles')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'dhcp.dhcp': {
            'Meta': {'object_name': 'DHCP', 'db_table': "u'dhcp_scopes'"},
            'allow_booting': ('django.db.models.fields.IntegerField', [], {'max_length': '32'}),
            'allow_bootp': ('django.db.models.fields.IntegerField', [], {'max_length': '32'}),
            'filename': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'option_domain_name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'option_domain_name_servers': ('django.db.models.fields.CharField', [], {'max_length': '48', 'null': 'True', 'blank': 'True'}),
            'option_ntp_servers': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'option_routers': ('django.db.models.fields.CharField', [], {'max_length': '16', 'null': 'True', 'blank': 'True'}),
            'option_subnet_mask': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'pool_deny_dynamic_bootp_agents': ('django.db.models.fields.IntegerField', [], {'max_length': '32'}),
            'pool_range_end': ('django.db.models.fields.CharField', [], {'max_length': '16', 'null': 'True', 'blank': 'True'}),
            'pool_range_start': ('django.db.models.fields.CharField', [], {'max_length': '16', 'null': 'True', 'blank': 'True'}),
            'scope_name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'scope_netmask': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'scope_notes': ('django.db.models.fields.TextField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'}),
            'scope_start': ('django.db.models.fields.CharField', [], {'max_length': '16', 'null': 'True', 'blank': 'True'})
        },
        'systems.advisorydata': {
            'Meta': {'object_name': 'AdvisoryData', 'db_table': "u'advisory_data'"},
            'advisory': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip_address': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'references': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'severity': ('django.db.models.fields.FloatField', [], {'blank': 'True'}),
            'title': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        'systems.allocation': {
            'Meta': {'ordering': "['name']", 'object_name': 'Allocation', 'db_table': "u'allocations'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'systems.contract': {
            'Meta': {'object_name': 'Contract', 'db_table': "u'contracts'"},
            'contract_link': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'contract_number': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'expiration': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'}),
            'support_level': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'system': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systems.System']"}),
            'updated_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        },
        'systems.keyvalue': {
            'Meta': {'object_name': 'KeyValue', 'db_table': "u'key_value'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'system': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systems.System']"}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        'systems.location': {
            'Meta': {'ordering': "['name']", 'object_name': 'Location', 'db_table': "u'locations'"},
            'address': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255', 'blank': 'True'}),
            'note': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
        },
        'systems.mac': {
            'Meta': {'object_name': 'Mac', 'db_table': "u'macs'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mac': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '17'}),
            'system': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systems.System']"})
        },
        'systems.networkadapter': {
            'Meta': {'object_name': 'NetworkAdapter', 'db_table': "u'network_adapters'"},
            'adapter_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'dhcp_scope': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dhcp.DHCP']", 'null': 'True', 'blank': 'True'}),
            'filename': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip_address': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'mac_address': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'option_domain_name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'option_host_name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'switch_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'switch_port': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'system_id': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'systems.operatingsystem': {
            'Meta': {'ordering': "['name', 'version']", 'object_name': 'OperatingSystem', 'db_table': "u'operating_systems'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        'systems.portdata': {
            'Meta': {'object_name': 'PortData', 'db_table': "u'port_data'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip_address': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'port': ('django.db.models.fields.IntegerField', [], {'blank': 'True'}),
            'protocol': ('django.db.models.fields.CharField', [], {'max_length': '3', 'blank': 'True'}),
            'service': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '13', 'blank': 'True'}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'})
        },
        'systems.scheduledtask': {
            'Meta': {'ordering': "['task']", 'object_name': 'ScheduledTask', 'db_table': "u'scheduled_tasks'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'task': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'systems.servermodel': {
            'Meta': {'ordering': "['vendor', 'model']", 'object_name': 'ServerModel', 'db_table': "u'server_models'"},
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'part_number': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'vendor': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        'systems.system': {
            'Meta': {'object_name': 'System', 'db_table': "u'systems'"},
            'allocation': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systems.Allocation']", 'null': 'True', 'blank': 'True'}),
            'asset_tag': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'change_password': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'hostname': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_dhcp_server': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'is_dns_server': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'is_nagios_server': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'is_puppet_server': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'is_switch': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'licenses': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'oob_ip': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'oob_switch_port': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'operating_system': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systems.OperatingSystem']", 'null': 'True', 'blank': 'True'}),
            'patch_panel_port': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'purchase_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'purchase_price': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'rack_order': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '2', 'blank': 'True'}),
            'ram': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'serial': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'server_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systems.ServerModel']", 'null': 'True', 'blank': 'True'}),
            'switch_ports': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'system_rack': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systems.SystemRack']", 'null': 'True', 'blank': 'True'}),
            'system_status': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systems.SystemStatus']", 'null': 'True', 'blank': 'True'}),
            'updated_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        },
        'systems.systemchangelog': {
            'Meta': {'object_name': 'SystemChangeLog', 'db_table': "u'systems_change_log'"},
            'changed_by': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'changed_date': ('django.db.models.fields.DateTimeField', [], {}),
            'changed_text': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'system': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systems.System']"})
        },
        'systems.systemrack': {
            'Meta': {'ordering': "['name']", 'object_name': 'SystemRack', 'db_table': "u'system_racks'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systems.Location']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        'systems.systemstatus': {
            'Meta': {'ordering': "['status']", 'object_name': 'SystemStatus', 'db_table': "u'system_statuses'"},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'color_code': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        'systems.systemtype': {
            'Meta': {'object_name': 'SystemType', 'db_table': "u'system_types'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        'systems.userprofile': {
            'Meta': {'object_name': 'UserProfile', 'db_table': "u'user_profiles'"},
            'api_key': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'current_desktop_oncall': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'current_services_oncall': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'current_sysadmin_oncall': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'epager_address': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'irc_nick': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'is_desktop_oncall': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_services_oncall': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_sysadmin_oncall': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'pager_number': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'pager_type': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'unique': 'True'})
        }
    }

    complete_apps = ['systems']