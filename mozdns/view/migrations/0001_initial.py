# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'View'
        db.create_table('view', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('view', ['View'])

        # Adding unique constraint on 'View', fields ['name']
        db.create_unique('view', ['name'])


    def backwards(self, orm):
        # Removing unique constraint on 'View', fields ['name']
        db.delete_unique('view', ['name'])

        # Deleting model 'View'
        db.delete_table('view')


    models = {
        'view.view': {
            'Meta': {'unique_together': "(('name',),)", 'object_name': 'View', 'db_table': "'view'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['view']