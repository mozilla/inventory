# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'SiteKeyValue.site'
        db.delete_column('site_key_value', 'site_id')

        # Adding field 'SiteKeyValue.obj'
        db.add_column('site_key_value', 'obj',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='keyvalue_set', to=orm['site.Site']),
                      keep_default=False)


    def backwards(self, orm):

        # User chose to not deal with backwards NULL issues for 'SiteKeyValue.site'
        raise RuntimeError("Cannot reverse this migration. 'SiteKeyValue.site' and its values cannot be restored.")
        # Deleting field 'SiteKeyValue.obj'
        db.delete_column('site_key_value', 'obj_id')


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
            'obj': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'keyvalue_set'", 'to': "orm['site.Site']"}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['site']