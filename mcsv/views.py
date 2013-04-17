from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import render

from mcsv.importer import Resolver, Generator
from mcsv.importer import csv_import
from systems.models import System


def csv_importer(request):
    r = Resolver()
    generator = Generator(r, [])
    return render(request, 'csv/csv_importer.html', {
        'generator': generator
    })


def ajax_csv_importer(request):
    save = True if request.POST.get('save', False) else False
    raw_csv_data = request.POST.get('csv-data', '')

    @transaction.commit_manually
    def do_csv_import(data):
        try:
            return csv_import(data, save=save)
        except ValidationError, e:
            transaction.rollback()
            return {'error': e.messages}
        except Exception, e:
            transaction.rollback()
            return {'error': ['Error: ' + e.message]}
        finally:
            transaction.commit()

    result = do_csv_import(raw_csv_data.split('\n'))

    attrs = [field.name for field in System._meta.fields]

    return render(request, 'csv/ajax_csv_importer.html', {
        'attrs': attrs,
        'result': result,
        'getattr': getattr,
        'save': save,
        'len': len
    })


def csv_format(request):
    r = Resolver()
    generator = Generator(r, [])
    return render(request, 'csv/csv_importer_help.html', {
        'generator': generator
    })
