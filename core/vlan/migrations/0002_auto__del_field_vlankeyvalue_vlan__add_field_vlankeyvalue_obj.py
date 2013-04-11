# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'VlanKeyValue.vlan'
        db.delete_column('vlan_key_value', 'vlan_id')

        # Adding field 'VlanKeyValue.obj'
        db.add_column('vlan_key_value', 'obj',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='keyvalue_set', to=orm['vlan.Vlan']),
                      keep_default=False)


    def backwards(self, orm):

        # User chose to not deal with backwards NULL issues for 'VlanKeyValue.vlan'
        raise RuntimeError("Cannot reverse this migration. 'VlanKeyValue.vlan' and its values cannot be restored.")
        # Deleting field 'VlanKeyValue.obj'
        db.delete_column('vlan_key_value', 'obj_id')


    models = {
        'vlan.vlan': {
            'Meta': {'unique_together': "(('name', 'number'),)", 'object_name': 'Vlan', 'db_table': "'vlan'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'number': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        'vlan.vlankeyvalue': {
            'Meta': {'unique_together': "(('key', 'value'),)", 'object_name': 'VlanKeyValue', 'db_table': "'vlan_key_value'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'obj': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'keyvalue_set'", 'to': "orm['vlan.Vlan']"}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['vlan']