# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        from django.db import connection
        sql = """
        ALTER TABLE `static` CHANGE `ip_upper` `ip_upper` BIGINT( 64 ) UNSIGNED;
        ALTER TABLE `static` CHANGE `ip_lower` `ip_lower` BIGINT( 64 ) UNSIGNED;
        """
        cursor = connection.cursor()
        cursor.execute(sql)

    def backwards(self, orm):
        pass
