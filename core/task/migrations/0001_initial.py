# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Task'
        db.create_table(u'task', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('task', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('ttype', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('task', ['Task'])


    def backwards(self, orm):
        # Deleting model 'Task'
        db.delete_table(u'task')


    models = {
        'task.task': {
            'Meta': {'ordering': "['task']", 'object_name': 'Task', 'db_table': "u'task'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'task': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'ttype': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['task']