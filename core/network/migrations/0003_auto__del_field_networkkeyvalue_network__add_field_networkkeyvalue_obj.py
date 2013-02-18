# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Removing unique constraint on 'NetworkKeyValue', fields ['value', 'key', 'network']
        db.delete_unique('network_key_value', ['value', 'key', 'network_id'])

        # Deleting field 'NetworkKeyValue.network'
        db.delete_column('network_key_value', 'network_id')

        # Adding field 'NetworkKeyValue.obj'
        db.add_column('network_key_value', 'obj',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='keyvalue_set', to=orm['network.Network']),
                      keep_default=False)

        # Adding unique constraint on 'NetworkKeyValue', fields ['obj', 'value', 'key']
        db.create_unique('network_key_value', ['obj_id', 'value', 'key'])


    def backwards(self, orm):
        # Removing unique constraint on 'NetworkKeyValue', fields ['obj', 'value', 'key']
        db.delete_unique('network_key_value', ['obj_id', 'value', 'key'])


        # User chose to not deal with backwards NULL issues for 'NetworkKeyValue.network'
        raise RuntimeError("Cannot reverse this migration. 'NetworkKeyValue.network' and its values cannot be restored.")
        # Deleting field 'NetworkKeyValue.obj'
        db.delete_column('network_key_value', 'obj_id')

        # Adding unique constraint on 'NetworkKeyValue', fields ['value', 'key', 'network']
        db.create_unique('network_key_value', ['value', 'key', 'network_id'])


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
            'Meta': {'unique_together': "(('key', 'value', 'obj'),)", 'object_name': 'NetworkKeyValue', 'db_table': "'network_key_value'"},
            'has_validator': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_option': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_statement': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'obj': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'keyvalue_set'", 'to': "orm['network.Network']"}),
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