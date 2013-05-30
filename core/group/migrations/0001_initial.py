# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Group'
        db.create_table('group', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('group', ['Group'])

        # Adding unique constraint on 'Group', fields ['name']
        db.create_unique('group', ['name'])

        # Adding model 'GroupKeyValue'
        db.create_table('group_key_value', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('obj', self.gf('django.db.models.fields.related.ForeignKey')(related_name='keyvalue_set', to=orm['group.Group'])),
        ))
        db.send_create_signal('group', ['GroupKeyValue'])

        # Adding unique constraint on 'GroupKeyValue', fields ['key', 'value']
        db.create_unique('group_key_value', ['key', 'value'])


    def backwards(self, orm):
        # Removing unique constraint on 'GroupKeyValue', fields ['key', 'value']
        db.delete_unique('group_key_value', ['key', 'value'])

        # Removing unique constraint on 'Group', fields ['name']
        db.delete_unique('group', ['name'])

        # Deleting model 'Group'
        db.delete_table('group')

        # Deleting model 'GroupKeyValue'
        db.delete_table('group_key_value')


    models = {
        'group.group': {
            'Meta': {'unique_together': "(('name',),)", 'object_name': 'Group', 'db_table': "'group'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'group.groupkeyvalue': {
            'Meta': {'unique_together': "(('key', 'value'),)", 'object_name': 'GroupKeyValue', 'db_table': "'group_key_value'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'obj': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'keyvalue_set'", 'to': "orm['group.Group']"}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['group']