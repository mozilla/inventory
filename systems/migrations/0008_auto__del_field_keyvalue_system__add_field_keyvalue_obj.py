# -*- coding: utf-8 -*-
from south.db import db
from south.v2 import SchemaMigration


class Migration(SchemaMigration):

    def forwards(self, orm):
        if not db.dry_run:
            db.rename_column('key_value', 'system_id', 'obj_id')

    def backwards(self, orm):
        if not db.dry_run:
            db.rename_column('key_value', 'obj_id', 'system_id')
