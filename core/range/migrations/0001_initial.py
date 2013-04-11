# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Range'
        db.create_table('range', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('start_upper', self.gf('django.db.models.fields.BigIntegerField')(null=True)),
            ('start_lower', self.gf('django.db.models.fields.BigIntegerField')(null=True)),
            ('start_str', self.gf('django.db.models.fields.CharField')(max_length=39)),
            ('end_lower', self.gf('django.db.models.fields.BigIntegerField')(null=True)),
            ('end_upper', self.gf('django.db.models.fields.BigIntegerField')(null=True)),
            ('end_str', self.gf('django.db.models.fields.CharField')(max_length=39)),
            ('dhcpd_raw_include', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('network', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['network.Network'])),
        ))
        db.send_create_signal('range', ['Range'])

        # Adding unique constraint on 'Range', fields ['start_upper', 'start_lower', 'end_upper', 'end_lower']
        db.create_unique('range', ['start_upper', 'start_lower', 'end_upper', 'end_lower'])

        # Adding model 'RangeKeyValue'
        db.create_table('range_key_value', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('is_option', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_statement', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('has_validator', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('range', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['range.Range'])),
        ))
        db.send_create_signal('range', ['RangeKeyValue'])

        # Adding unique constraint on 'RangeKeyValue', fields ['key', 'value', 'range']
        db.create_unique('range_key_value', ['key', 'value', 'range_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'RangeKeyValue', fields ['key', 'value', 'range']
        db.delete_unique('range_key_value', ['key', 'value', 'range_id'])

        # Removing unique constraint on 'Range', fields ['start_upper', 'start_lower', 'end_upper', 'end_lower']
        db.delete_unique('range', ['start_upper', 'start_lower', 'end_upper', 'end_lower'])

        # Deleting model 'Range'
        db.delete_table('range')

        # Deleting model 'RangeKeyValue'
        db.delete_table('range_key_value')


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
        'range.range': {
            'Meta': {'unique_together': "(('start_upper', 'start_lower', 'end_upper', 'end_lower'),)", 'object_name': 'Range', 'db_table': "'range'"},
            'dhcpd_raw_include': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'end_lower': ('django.db.models.fields.BigIntegerField', [], {'null': 'True'}),
            'end_str': ('django.db.models.fields.CharField', [], {'max_length': '39'}),
            'end_upper': ('django.db.models.fields.BigIntegerField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'network': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['network.Network']"}),
            'start_lower': ('django.db.models.fields.BigIntegerField', [], {'null': 'True'}),
            'start_str': ('django.db.models.fields.CharField', [], {'max_length': '39'}),
            'start_upper': ('django.db.models.fields.BigIntegerField', [], {'null': 'True'})
        },
        'range.rangekeyvalue': {
            'Meta': {'unique_together': "(('key', 'value', 'range'),)", 'object_name': 'RangeKeyValue', 'db_table': "'range_key_value'"},
            'has_validator': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_option': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_statement': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'range': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['range.Range']"}),
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

    complete_apps = ['range']