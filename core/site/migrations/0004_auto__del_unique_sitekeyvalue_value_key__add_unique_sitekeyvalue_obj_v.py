# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Removing unique constraint on 'SiteKeyValue', fields ['value', 'key']
        db.delete_unique('site_key_value', ['value', 'key'])

        # Adding unique constraint on 'SiteKeyValue', fields ['obj', 'value', 'key']
        db.create_unique('site_key_value', ['obj_id', 'value', 'key'])


    def backwards(self, orm):
        # Removing unique constraint on 'SiteKeyValue', fields ['obj', 'value', 'key']
        db.delete_unique('site_key_value', ['obj_id', 'value', 'key'])

        # Adding unique constraint on 'SiteKeyValue', fields ['value', 'key']
        db.create_unique('site_key_value', ['value', 'key'])


    models = {
        'site.site': {
            'Meta': {'unique_together': "(('name', 'parent'),)", 'object_name': 'Site', 'db_table': "'site'"},
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