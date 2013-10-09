from django.http import HttpResponse

from systems.models import System

from core.search.compiler.django_compile import compile_to_q

from MySQLdb import OperationalError
from bulk_action.import_utils import loads, dumps, system_import, BadImportData

import pprint


def bulk_import(main_blob):
    try:
        blobs = loads(main_blob)
    except ValueError, e:  # Can't find JSONDecodeError
        return HttpResponse(dumps({'errors': str(e)}))
    if not isinstance(blobs, list):
        return HttpResponse(
            dumps({'errors': 'Main JSON blob must be a list of systems'})
        )
    for i, s_blob in enumerate(blobs):
        try:
            save_functions = system_import(s_blob)
            for priority, fn in sorted(save_functions, key=lambda f: f[0]):
                fn()
        except BadImportData, e:
            return HttpResponse(dumps({
                'errors': 'Found an issue while processing the {0} system '
                'blob: {1}.\nBad blob was:\n{2}'.format(i, e.msg, e.bad_blob)
            }))

    return blobs


def bulk_action_import(request):
    blob = request.POST.get('blob', None)
    if not blob:
        return HttpResponse(dumps({'errors': 'what do you want?'}))
    return HttpResponse(bulk_import(blob))


def bulk_action_export(request):
    search = request.GET.get('q', '')
    if not search:
        return HttpResponse(dumps({'errors': 'what do you want?'}))
    q_map, errors = compile_to_q(search)
    if errors:
        return HttpResponse(dumps({'errors': errors}))

    try:  # We might have to catch shitty regular expressions
        bundles = System.get_bulk_action_list(q_map['SYS'])
    except OperationalError as why:
        return HttpResponse(dumps({'error_messages': str(why)}))

    pprint.pprint(bundles)
    return HttpResponse(dumps({'text_response': bundles}))
