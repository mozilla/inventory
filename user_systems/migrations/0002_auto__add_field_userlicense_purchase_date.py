# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'UserLicense.purchase_date'
        db.add_column(u'user_licenses', 'purchase_date',
                      self.gf('django.db.models.fields.DateField')(default=None, null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'UserLicense.purchase_date'
        db.delete_column(u'user_licenses', 'purchase_date')


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
            'purchase_date': ('django.db.models.fields.DateField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
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