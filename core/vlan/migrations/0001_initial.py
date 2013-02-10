# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Vlan'
        db.create_table('vlan', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('number', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal('vlan', ['Vlan'])

        # Adding unique constraint on 'Vlan', fields ['name', 'number']
        db.create_unique('vlan', ['name', 'number'])

        # Adding model 'VlanKeyValue'
        db.create_table('vlan_key_value', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('vlan', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['vlan.Vlan'])),
        ))
        db.send_create_signal('vlan', ['VlanKeyValue'])

        # Adding unique constraint on 'VlanKeyValue', fields ['key', 'value']
        db.create_unique('vlan_key_value', ['key', 'value'])


    def backwards(self, orm):
        # Removing unique constraint on 'VlanKeyValue', fields ['key', 'value']
        db.delete_unique('vlan_key_value', ['key', 'value'])

        # Removing unique constraint on 'Vlan', fields ['name', 'number']
        db.delete_unique('vlan', ['name', 'number'])

        # Deleting model 'Vlan'
        db.delete_table('vlan')

        # Deleting model 'VlanKeyValue'
        db.delete_table('vlan_key_value')


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
            'value': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'vlan': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['vlan.Vlan']"})
        }
    }

    complete_apps = ['vlan']