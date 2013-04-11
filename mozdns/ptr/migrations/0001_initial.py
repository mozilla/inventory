# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'PTR'
        db.create_table('ptr', (
            ('ip_str', self.gf('django.db.models.fields.CharField')(max_length=39)),
            ('ip_upper', self.gf('django.db.models.fields.BigIntegerField')(null=True, blank=True)),
            ('ip_lower', self.gf('django.db.models.fields.BigIntegerField')(null=True, blank=True)),
            ('ip_type', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('ttl', self.gf('django.db.models.fields.PositiveIntegerField')(default=3600, null=True, blank=True)),
            ('reverse_domain', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['domain.Domain'], blank=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=1000, null=True, blank=True)),
        ))
        db.send_create_signal('ptr', ['PTR'])

        # Adding unique constraint on 'PTR', fields ['ip_str', 'ip_type', 'name']
        db.create_unique('ptr', ['ip_str', 'ip_type', 'name'])

        # Adding M2M table for field views on 'PTR'
        db.create_table('ptr_views', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('ptr', models.ForeignKey(orm['ptr.ptr'], null=False)),
            ('view', models.ForeignKey(orm['view.view'], null=False))
        ))
        db.create_unique('ptr_views', ['ptr_id', 'view_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'PTR', fields ['ip_str', 'ip_type', 'name']
        db.delete_unique('ptr', ['ip_str', 'ip_type', 'name'])

        # Deleting model 'PTR'
        db.delete_table('ptr')

        # Removing M2M table for field views on 'PTR'
        db.delete_table('ptr_views')


    models = {
        'domain.domain': {
            'Meta': {'object_name': 'Domain', 'db_table': "'domain'"},
            'delegated': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'dirty': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_reverse': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'master_domain': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['domain.Domain']", 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'purgeable': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'soa': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['soa.SOA']", 'null': 'True', 'blank': 'True'})
        },
        'ptr.ptr': {
            'Meta': {'unique_together': "(('ip_str', 'ip_type', 'name'),)", 'object_name': 'PTR', 'db_table': "'ptr'"},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip_lower': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'ip_str': ('django.db.models.fields.CharField', [], {'max_length': '39'}),
            'ip_type': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'ip_upper': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'reverse_domain': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['domain.Domain']", 'blank': 'True'}),
            'ttl': ('django.db.models.fields.PositiveIntegerField', [], {'default': '3600', 'null': 'True', 'blank': 'True'}),
            'views': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['view.View']", 'symmetrical': 'False', 'blank': 'True'})
        },
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
            'serial': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1360538202'}),
            'ttl': ('django.db.models.fields.PositiveIntegerField', [], {'default': '3600', 'null': 'True', 'blank': 'True'})
        },
        'view.view': {
            'Meta': {'unique_together': "(('name',),)", 'object_name': 'View', 'db_table': "'view'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['ptr']