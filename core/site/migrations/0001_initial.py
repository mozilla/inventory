# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Site'
        db.create_table('site', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['site.Site'], null=True, blank=True)),
        ))
        db.send_create_signal('site', ['Site'])

        # Adding unique constraint on 'Site', fields ['name', 'parent']
        db.create_unique('site', ['name', 'parent_id'])

        # Adding model 'SiteKeyValue'
        db.create_table('site_key_value', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('site', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['site.Site'])),
        ))
        db.send_create_signal('site', ['SiteKeyValue'])

        # Adding unique constraint on 'SiteKeyValue', fields ['key', 'value']
        db.create_unique('site_key_value', ['key', 'value'])


    def backwards(self, orm):
        # Removing unique constraint on 'SiteKeyValue', fields ['key', 'value']
        db.delete_unique('site_key_value', ['key', 'value'])

        # Removing unique constraint on 'Site', fields ['name', 'parent']
        db.delete_unique('site', ['name', 'parent_id'])

        # Deleting model 'Site'
        db.delete_table('site')

        # Deleting model 'SiteKeyValue'
        db.delete_table('site_key_value')


    models = {
        'site.site': {
            'Meta': {'unique_together': "(('name', 'parent'),)", 'object_name': 'Site', 'db_table': "'site'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['site.Site']", 'null': 'True', 'blank': 'True'})
        },
        'site.sitekeyvalue': {
            'Meta': {'unique_together': "(('key', 'value'),)", 'object_name': 'SiteKeyValue', 'db_table': "'site_key_value'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['site.Site']"}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['site']