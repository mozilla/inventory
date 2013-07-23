# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Removing unique constraint on 'Site', fields ['name', 'parent']
        db.delete_unique('site', ['name', 'parent_id'])

        # Adding unique constraint on 'Site', fields ['full_name']
        db.create_unique('site', ['full_name'])


    def backwards(self, orm):
        # Removing unique constraint on 'Site', fields ['full_name']
        db.delete_unique('site', ['full_name'])

        # Adding unique constraint on 'Site', fields ['name', 'parent']
        db.create_unique('site', ['name', 'parent_id'])


    models = {
        'site.site': {
            'Meta': {'unique_together': "(('full_name',),)", 'object_name': 'Site', 'db_table': "'site'"},
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['site.Site']", 'null': 'True', 'blank': 'True'})
        },
        'site.sitekeyvalue': {
            'Meta': {'unique_together': "(('key', 'value', 'obj'),)", 'object_name': 'SiteKeyValue', 'db_table': "'site_key_value'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'obj': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'keyvalue_set'", 'to': "orm['site.Site']"}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['site']