# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'DNSBuildRun'
        db.create_table('mozbind_dnsbuildrun', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('log', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('mozbind', ['DNSBuildRun'])

        # Adding model 'BuildManifest'
        db.create_table('mozbind_buildmanifest', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('zname', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('files', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('zhash', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('build_run', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mozbind.DNSBuildRun'])),
        ))
        db.send_create_signal('mozbind', ['BuildManifest'])


    def backwards(self, orm):
        # Deleting model 'DNSBuildRun'
        db.delete_table('mozbind_dnsbuildrun')

        # Deleting model 'BuildManifest'
        db.delete_table('mozbind_buildmanifest')


    models = {
        'mozbind.buildmanifest': {
            'Meta': {'object_name': 'BuildManifest'},
            'build_run': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mozbind.DNSBuildRun']"}),
            'files': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'zhash': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'zname': ('django.db.models.fields.CharField', [], {'max_length': '256'})
        },
        'mozbind.dnsbuildrun': {
            'Meta': {'object_name': 'DNSBuildRun'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'log': ('django.db.models.fields.TextField', [], {})
        }
    }

    complete_apps = ['mozbind']