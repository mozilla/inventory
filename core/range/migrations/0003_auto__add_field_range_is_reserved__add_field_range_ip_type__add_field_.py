# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Removing unique constraint on 'RangeKeyValue', fields ['range', 'value', 'key']
        db.delete_unique('range_key_value', ['range_id', 'value', 'key'])

        # Adding field 'Range.is_reserved'
        db.add_column('range', 'is_reserved',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'Range.ip_type'
        db.add_column('range', 'ip_type',
                      self.gf('django.db.models.fields.CharField')(max_length=1, null=True),
                      keep_default=False)

        # Adding field 'Range.rtype'
        db.add_column('range', 'rtype',
                      self.gf('django.db.models.fields.CharField')(default='st', max_length=2),
                      keep_default=False)

        # Deleting field 'RangeKeyValue.range'
        db.delete_column('range_key_value', 'range_id')

        # Adding field 'RangeKeyValue.obj'
        db.add_column('range_key_value', 'obj',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='keyvalue_set', to=orm['range.Range']),
                      keep_default=False)

        # Adding unique constraint on 'RangeKeyValue', fields ['obj', 'value', 'key']
        db.create_unique('range_key_value', ['obj_id', 'value', 'key'])


    def backwards(self, orm):
        # Removing unique constraint on 'RangeKeyValue', fields ['obj', 'value', 'key']
        db.delete_unique('range_key_value', ['obj_id', 'value', 'key'])

        # Deleting field 'Range.is_reserved'
        db.delete_column('range', 'is_reserved')

        # Deleting field 'Range.ip_type'
        db.delete_column('range', 'ip_type')

        # Deleting field 'Range.rtype'
        db.delete_column('range', 'rtype')


        # User chose to not deal with backwards NULL issues for 'RangeKeyValue.range'
        raise RuntimeError("Cannot reverse this migration. 'RangeKeyValue.range' and its values cannot be restored.")
        # Deleting field 'RangeKeyValue.obj'
        db.delete_column('range_key_value', 'obj_id')

        # Adding unique constraint on 'RangeKeyValue', fields ['range', 'value', 'key']
        db.create_unique('range_key_value', ['range_id', 'value', 'key'])


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
            'ip_type': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True'}),
            'is_reserved': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'network': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['network.Network']"}),
            'rtype': ('django.db.models.fields.CharField', [], {'default': "'st'", 'max_length': '2'}),
            'start_lower': ('django.db.models.fields.BigIntegerField', [], {'null': 'True'}),
            'start_str': ('django.db.models.fields.CharField', [], {'max_length': '39'}),
            'start_upper': ('django.db.models.fields.BigIntegerField', [], {'null': 'True'})
        },
        'range.rangekeyvalue': {
            'Meta': {'unique_together': "(('key', 'value', 'obj'),)", 'object_name': 'RangeKeyValue', 'db_table': "'range_key_value'"},
            'has_validator': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_option': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_statement': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'obj': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'keyvalue_set'", 'to': "orm['range.Range']"}),
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