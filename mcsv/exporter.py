from django.db.utils import DatabaseError
from django.core.exceptions import ObjectDoesNotExist

import user_systems
import systems

import csv
import cStringIO
import re

export_classes = dict(map(
    lambda c: (c.__name__, c),
    [
        user_systems.models.UserLicense,
        user_systems.models.UnmanagedSystem,
        systems.models.System,
    ]
))


def csv_export(Klass):
    if hasattr(Klass, 'csv_attr_ignore'):
        attr_ignore = Klass.csv_attr_ignore
    else:
        attr_ignore = []
    obj_fields = [
        field.name
        for field in Klass._meta.fields
        if field.name not in attr_ignore
    ]

    queue = cStringIO.StringIO()
    queue.write(','.join(obj_fields) + '\n')
    out = csv.writer(
        queue, dialect='excel', lineterminator='\n'
    )
    try:
        for obj in Klass.objects.all():
            row = []
            for field in obj_fields:
                try:
                    value = getattr(obj, field)
                except ObjectDoesNotExist:
                    # Some fields are missing FK validaiton
                    value = None

                if field == 'licenses':
                    if value:
                        value = re.escape(value)
                    else:
                        value = ''
                try:
                    row.append(str(value))
                except:
                    row.append(value.encode('utf-8'))
            out.writerow(row)
    except DatabaseError as why:
        return None, why
    except Exception as why:
        return None, why

    queue.seek(0)
    return queue, None
