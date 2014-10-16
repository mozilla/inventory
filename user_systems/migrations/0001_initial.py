# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'UserOperatingSystem'
        db.create_table('user_systems_useroperatingsystem', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
        ))
        db.send_create_signal('user_systems', ['UserOperatingSystem'])

        # Adding model 'UnmanagedSystemType'
        db.create_table('unmanaged_system_types', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
        ))
        db.send_create_signal('user_systems', ['UnmanagedSystemType'])

        # Adding model 'CostCenter'
        db.create_table('cost_centers', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('cost_center_number', self.gf('django.db.models.fields.IntegerField')()),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
        ))
        db.send_create_signal('user_systems', ['CostCenter'])

        # Adding model 'UnmanagedSystem'
        db.create_table(u'unmanaged_systems', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('serial', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('asset_tag', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('operating_system', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['systems.OperatingSystem'], null=True, blank=True)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['user_systems.Owner'], null=True, blank=True)),
            ('system_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['user_systems.UnmanagedSystemType'], null=True)),
            ('server_model', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['systems.ServerModel'], null=True, blank=True)),
            ('created_on', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('updated_on', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('date_purchased', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('cost', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('cost_center', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['user_systems.CostCenter'], null=True, blank=True)),
            ('bug_number', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('notes', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('is_loaned', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('is_loaner', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('loaner_return_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal('user_systems', ['UnmanagedSystem'])

        # Adding model 'History'
        db.create_table('user_systems_history', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('change', self.gf('django.db.models.fields.CharField')(max_length=1000)),
            ('changed_by', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
            ('system', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['user_systems.UnmanagedSystem'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('user_systems', ['History'])

        # Adding model 'Owner'
        db.create_table(u'owners', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255, blank=True)),
            ('address', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('note', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('user_location', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['user_systems.UserLocation'], null=True, blank=True)),
            ('email', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
        ))
        db.send_create_signal('user_systems', ['Owner'])

        # Adding model 'UserLicense'
        db.create_table(u'user_licenses', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('username', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('version', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('license_type', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('license_key', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['user_systems.Owner'], null=True, blank=True)),
            ('user_operating_system', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['user_systems.UserOperatingSystem'], null=True, blank=True)),
        ))
        db.send_create_signal('user_systems', ['UserLicense'])

        # Adding model 'UserLocation'
        db.create_table(u'user_locations', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('city', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255, blank=True)),
            ('country', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255, blank=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal('user_systems', ['UserLocation'])


    def backwards(self, orm):
        # Deleting model 'UserOperatingSystem'
        db.delete_table('user_systems_useroperatingsystem')

        # Deleting model 'UnmanagedSystemType'
        db.delete_table('unmanaged_system_types')

        # Deleting model 'CostCenter'
        db.delete_table('cost_centers')

        # Deleting model 'UnmanagedSystem'
        db.delete_table(u'unmanaged_systems')

        # Deleting model 'History'
        db.delete_table('user_systems_history')

        # Deleting model 'Owner'
        db.delete_table(u'owners')

        # Deleting model 'UserLicense'
        db.delete_table(u'user_licenses')

        # Deleting model 'UserLocation'
        db.delete_table(u'user_locations')


    models = {
        'systems.operatingsystem': {
            'Meta': {'ordering': "['name', 'version']", 'object_name': 'OperatingSystem', 'db_table': "u'operating_systems'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        'systems.servermodel': {
            'Meta': {'ordering': "['vendor', 'model']", 'object_name': 'ServerModel', 'db_table': "u'server_models'"},
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'part_number': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'vendor': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        'user_systems.costcenter': {
            'Meta': {'object_name': 'CostCenter', 'db_table': "'cost_centers'"},
            'cost_center_number': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        'user_systems.history': {
            'Meta': {'ordering': "['-created']", 'object_name': 'History'},
            'change': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'changed_by': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'system': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['user_systems.UnmanagedSystem']"})
        },
        'user_systems.owner': {
            'Meta': {'ordering': "['name']", 'object_name': 'Owner', 'db_table': "u'owners'"},
            'address': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'email': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255', 'blank': 'True'}),
            'note': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'user_location': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['user_systems.UserLocation']", 'null': 'True', 'blank': 'True'})
        },
        'user_systems.unmanagedsystem': {
            'Meta': {'object_name': 'UnmanagedSystem', 'db_table': "u'unmanaged_systems'"},
            'asset_tag': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'bug_number': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'cost': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'cost_center': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['user_systems.CostCenter']", 'null': 'True', 'blank': 'True'}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'date_purchased': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_loaned': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'is_loaner': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'loaner_return_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'operating_system': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systems.OperatingSystem']", 'null': 'True', 'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['user_systems.Owner']", 'null': 'True', 'blank': 'True'}),
            'serial': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'server_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['systems.ServerModel']", 'null': 'True', 'blank': 'True'}),
            'system_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['user_systems.UnmanagedSystemType']", 'null': 'True'}),
            'updated_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        },
        'user_systems.unmanagedsystemtype': {
            'Meta': {'object_name': 'UnmanagedSystemType', 'db_table': "'unmanaged_system_types'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'user_systems.userlicense': {
            'Meta': {'ordering': "['license_type']", 'object_name': 'UserLicense', 'db_table': "u'user_licenses'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'license_key': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'license_type': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['user_systems.Owner']", 'null': 'True', 'blank': 'True'}),
            'user_operating_system': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['user_systems.UserOperatingSystem']", 'null': 'True', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        'user_systems.userlocation': {
            'Meta': {'object_name': 'UserLocation', 'db_table': "u'user_locations'"},
            'city': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255', 'blank': 'True'}),
            'country': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        },
        'user_systems.useroperatingsystem': {
            'Meta': {'object_name': 'UserOperatingSystem'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        }
    }

    complete_apps = ['user_systems']