from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.utils import DatabaseError
from django.shortcuts import render
from django.http import HttpResponse

from mcsv.importer import csv_import, Resolver, Generator
from mcsv.exporter import csv_export, export_classes

from systems.models import System

from core.search.compiler.django_compile import compile_to_django

import csv
import re
import cStringIO
import simplejson as json


def csv_importer(request):
    r = Resolver()
    generator = Generator(r, [])
    return render(request, 'csv/csv_importer.html', {
        'generator': generator
    })


def ajax_csv_importer(request):
    save = True if request.POST.get('save', False) else False
    raw_csv_data = request.POST.get('csv-data', '')
    primary_attr = request.POST.get('primary-attr', 'hostname')

    @transaction.commit_manually
    def do_csv_import(data):
        try:
            return csv_import(data, primary_attr=primary_attr, save=save)
        except ValidationError, e:
            transaction.rollback()
            return {'error': e.messages}
        except Exception, e:
            transaction.rollback()
            return {'error': ['Error: ' + e.message]}
        finally:
            transaction.commit()

    result = do_csv_import(raw_csv_data)

    attrs = [field.name for field in System._meta.fields]

    return render(request, 'csv/ajax_csv_importer.html', {
        'attrs': attrs,
        'result': result,
        'getattr': getattr,
        'save': save,
        'len': len
    }, status=200 if 'error' not in result else 400)


def csv_format(request):
    r = Resolver()
    generator = Generator(r, [])
    return render(request, 'csv/csv_importer_help.html', {
        'generator': generator
    })


def ajax_csv_exporter(request):
    search = request.GET.get('search', None)

    if not search:
        return HttpResponse('What do you want?!?', status=400)

    obj_map, error_resp = compile_to_django(search)
    if not obj_map:
        return HttpResponse(
            json.dumps({'error_messages': error_resp}),
            status=400
        )

    attr_ignore = ('notes', 'licenses')

    systems = obj_map['SYS']

    system_fields = [
        field.name
        for field in System._meta.fields
        if field.name not in attr_ignore
    ]

    queue = cStringIO.StringIO()
    queue.write(','.join(system_fields) + '\n')
    out = csv.writer(
        queue, dialect='excel', lineterminator='\n'
    )
    try:
        for system in systems:
            row = []
            for field in system_fields:
                value = getattr(system, field)
                if field == 'licenses':
                    value = re.escape(value)
                row.append(str(value))
            out.writerow(row)
    except DatabaseError as why:
        return HttpResponse(
            json.dumps({'error_messages': str(why)}),
            status=400
        )

    queue.seek(0)
    return HttpResponse(json.dumps({'csv_content': queue.readlines()}))


def full_csv_exporter(request):
    return render(request, 'csv/csv_exporter.html', {
        'export_classes': export_classes.iteritems(),
    })


def ajax_full_csv_exporter(request):
    class_name = request.GET.get("class_name", None)
    if not class_name:
        return HttpResponse(
            "No class name provided",
            status=400
        )

    klass = export_classes.get(class_name, None)

    if not klass:
        return HttpResponse(
            "No class names '{0}'".format(class_name),
            status=400
        )

    output, errors = csv_export(klass)
    if errors:
        return HttpResponse(errors, status=400)

    return HttpResponse(output.readlines(), status=200)


def ajax_csv_export_classes(request):
    return HttpResponse(json.dumps(export_classes.keys()), status=200)
