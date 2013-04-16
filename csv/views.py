import simplejson as json

from django.db import transaction
from django.shortcuts import render

from csv.importer import Resolver, Generator
from csv.importer import csv_import
from systems.models import System


def csv_importer(request):
    r = Resolver()
    generator = Generator(r, [])
    return render(request, 'csv/csv_importer.html', {
        'generator': generator
    })

def ajax_csv_importer(request):
    save = request.POST.get('save', False)
    raw_csv_data = request.POST.get('csv-data', '')

    @transaction.commit_manually
    def do_csv_import(data):
        try:
            result = csv_import(data, save=True if save else False)
        except Exception, e:
            transaction.rollback()
            return {'error': e.message}
        transaction.commit()
        return result

    result = do_csv_import(raw_csv_data.split('\n'))

    import pdb;pdb.set_trace()
    attrs = System._meta.get_all_field_names()
    bad_attrs = ['buildattribute']
    for bad_attr in bad_attrs:
        attrs.remove(bad_attr)

    return render(request, 'csv/ajax_csv_importer.html', {
        'attrs': attrs,
        'result': result,
        'getattr': getattr
    })

def csv_format(request):
    r = Resolver()
    generator = Generator(r, [])
    return render(request, 'csv/csv_importer_help.html', {
        'generator': generator
    })
