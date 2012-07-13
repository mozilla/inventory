# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'RangeKeyValue.start'
        db.add_column('range_key_value', 'start',
                      self.gf('django.db.models.fields.PositiveIntegerField')(null=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'RangeKeyValue.start'
        db.delete_column('range_key_value', 'start')


    models = {
        'network.network': {
            'Meta': {'unique_together': "(('ip_upper', 'ip_lower', 'prefixlen'),)", 'object_name': 'Network', 'db_table': "'network'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip_lower': ('django.db.models.fields.BigIntegerField', [], {'blank': 'True'}),
            'ip_type': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'ip_upper': ('django.db.models.fields.BigIntegerField', [], {'blank': 'True'}),
            'network_str': ('django.db.models.fields.CharField', [], {'max_length': '39'}),
            'prefixlen': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['site.Site']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'vlan': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['vlan.Vlan']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'})
        },
        'range.range': {
            'Meta': {'unique_together': "(('start', 'end'),)", 'object_name': 'Range', 'db_table': "'range'"},
            'end': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'end_str': ('django.db.models.fields.CharField', [], {'max_length': '39'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'network': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['network.Network']"}),
            'start': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'start_str': ('django.db.models.fields.CharField', [], {'max_length': '39'})
        },
        'range.rangekeyvalue': {
            'Meta': {'unique_together': "(('key', 'value'),)", 'object_name': 'RangeKeyValue', 'db_table': "'range_key_value'"},
            'has_validator': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_option': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_statement': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'range': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['range.Range']"}),
            'start': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
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