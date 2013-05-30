# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'GroupKeyValue.is_option'
        db.add_column('group_key_value', 'is_option',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'GroupKeyValue.is_statement'
        db.add_column('group_key_value', 'is_statement',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'GroupKeyValue.has_validator'
        db.add_column('group_key_value', 'has_validator',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'GroupKeyValue.is_option'
        db.delete_column('group_key_value', 'is_option')

        # Deleting field 'GroupKeyValue.is_statement'
        db.delete_column('group_key_value', 'is_statement')

        # Deleting field 'GroupKeyValue.has_validator'
        db.delete_column('group_key_value', 'has_validator')


    models = {
        'group.group': {
            'Meta': {'unique_together': "(('name',),)", 'object_name': 'Group', 'db_table': "'group'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'group.groupkeyvalue': {
            'Meta': {'unique_together': "(('key', 'value'),)", 'object_name': 'GroupKeyValue', 'db_table': "'group_key_value'"},
            'has_validator': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_option': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_statement': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'obj': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'keyvalue_set'", 'to': "orm['group.Group']"}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['group']