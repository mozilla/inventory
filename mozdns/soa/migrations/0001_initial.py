# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'SOA'
        db.create_table('soa', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ttl', self.gf('django.db.models.fields.PositiveIntegerField')(default=3600, null=True, blank=True)),
            ('primary', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('contact', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('serial', self.gf('django.db.models.fields.PositiveIntegerField')(default=1360538203)),
            ('expire', self.gf('django.db.models.fields.PositiveIntegerField')(default=1209600)),
            ('retry', self.gf('django.db.models.fields.PositiveIntegerField')(default=86400)),
            ('refresh', self.gf('django.db.models.fields.PositiveIntegerField')(default=180)),
            ('minimum', self.gf('django.db.models.fields.PositiveIntegerField')(default=180)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('dirty', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('soa', ['SOA'])

        # Adding unique constraint on 'SOA', fields ['primary', 'contact', 'description']
        db.create_unique('soa', ['primary', 'contact', 'description'])

        # Adding model 'SOAKeyValue'
        db.create_table('soa_soakeyvalue', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('soa', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['soa.SOA'])),
        ))
        db.send_create_signal('soa', ['SOAKeyValue'])


    def backwards(self, orm):
        # Removing unique constraint on 'SOA', fields ['primary', 'contact', 'description']
        db.delete_unique('soa', ['primary', 'contact', 'description'])

        # Deleting model 'SOA'
        db.delete_table('soa')

        # Deleting model 'SOAKeyValue'
        db.delete_table('soa_soakeyvalue')


    models = {
        'soa.soa': {
            'Meta': {'unique_together': "(('primary', 'contact', 'description'),)", 'object_name': 'SOA', 'db_table': "'soa'"},
            'contact': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'dirty': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'expire': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1209600'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'minimum': ('django.db.models.fields.PositiveIntegerField', [], {'default': '180'}),
            'primary': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'refresh': ('django.db.models.fields.PositiveIntegerField', [], {'default': '180'}),
            'retry': ('django.db.models.fields.PositiveIntegerField', [], {'default': '86400'}),
            'serial': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1360538203'}),
            'ttl': ('django.db.models.fields.PositiveIntegerField', [], {'default': '3600', 'null': 'True', 'blank': 'True'})
        },
        'soa.soakeyvalue': {
            'Meta': {'object_name': 'SOAKeyValue'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'soa': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['soa.SOA']"}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['soa']