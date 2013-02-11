# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Network'
        db.create_table('network', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('vlan', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['vlan.Vlan'], null=True, on_delete=models.SET_NULL, blank=True)),
            ('site', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['site.Site'], null=True, on_delete=models.SET_NULL, blank=True)),
            ('ip_type', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('ip_upper', self.gf('django.db.models.fields.BigIntegerField')(blank=True)),
            ('ip_lower', self.gf('django.db.models.fields.BigIntegerField')(blank=True)),
            ('network_str', self.gf('django.db.models.fields.CharField')(max_length=49)),
            ('prefixlen', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('dhcpd_raw_include', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('network', ['Network'])

        # Adding unique constraint on 'Network', fields ['ip_upper', 'ip_lower', 'prefixlen']
        db.create_unique('network', ['ip_upper', 'ip_lower', 'prefixlen'])

        # Adding model 'NetworkKeyValue'
        db.create_table('network_key_value', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('is_option', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_statement', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('has_validator', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('network', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['network.Network'])),
        ))
        db.send_create_signal('network', ['NetworkKeyValue'])

        # Adding unique constraint on 'NetworkKeyValue', fields ['key', 'value', 'network']
        db.create_unique('network_key_value', ['key', 'value', 'network_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'NetworkKeyValue', fields ['key', 'value', 'network']
        db.delete_unique('network_key_value', ['key', 'value', 'network_id'])

        # Removing unique constraint on 'Network', fields ['ip_upper', 'ip_lower', 'prefixlen']
        db.delete_unique('network', ['ip_upper', 'ip_lower', 'prefixlen'])

        # Deleting model 'Network'
        db.delete_table('network')

        # Deleting model 'NetworkKeyValue'
        db.delete_table('network_key_value')


    models = {
        'network.network': {
            'Meta': {'unique_together': "(('ip_upper', 'ip_lower', 'prefixlen'),)", 'object_name': 'Network', 'db_table': "'network'"},
            'dhcpd_raw_include': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip_lower': ('django.db.models.fields.BigIntegerField', [], {'blank': 'True'}),
            'ip_type': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'ip_upper': ('django.db.models.fields.BigIntegerField', [], {'blank': 'True'}),
            'network_str': ('django.db.models.fields.CharField', [], {'max_length': '49'}),
            'prefixlen': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['site.Site']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'vlan': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['vlan.Vlan']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'})
        },
        'network.networkkeyvalue': {
            'Meta': {'unique_together': "(('key', 'value', 'network'),)", 'object_name': 'NetworkKeyValue', 'db_table': "'network_key_value'"},
            'has_validator': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_option': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_statement': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'network': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['network.Network']"}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'site.site': {
            'Meta': {'unique_together': "(('name', 'parent'),)", 'object_name': 'Site', 'db_table': "'site'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['site.Site']", 'null': 'True', 'blank': 'True'})
        },
        'vlan.vlan': {
            'Meta': {'unique_together': "(('name', 'number'),)", 'object_name': 'Vlan', 'db_table': "'vlan'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'number': ('django.db.models.fields.PositiveIntegerField', [], {})
        }
    }

    complete_apps = ['network']