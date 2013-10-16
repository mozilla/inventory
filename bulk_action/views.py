from django.http import HttpResponse
from django.core.exceptions import ValidationError
from django.db import transaction

from systems.models import System

from core.search.compiler.django_compile import compile_to_q

from MySQLdb import OperationalError
from bulk_action.import_utils import loads, dumps, system_import, BadImportData

import pprint
import simplejson as json


def bulk_import(main_blob, load_json=True):
    try:
        if load_json:
            json_blob = loads(main_blob)
        else:
            json_blob = main_blob
    except ValueError, e:  # Can't find JSONDecodeError
        return None, {'errors': str(e)}
    try:
        systems = json_blob['systems']
    except (KeyError, TypeError):
        return None, {'errors': 'Main JSON needs to have a key "systems".'}

    if not isinstance(systems, list):
        return None, {'errors': 'Main JSON blob must be a list of systems'}

    @transaction.commit_manually
    def do_import():
        try:
            for i, s_blob in enumerate(systems):
                save_functions = sorted(
                    system_import(s_blob), key=lambda f: f[0]
                )
                for priority, fn in save_functions:
                    fn()
        except BadImportData, e:
            transaction.rollback()
            return None, {
                'errors': 'Found an issue while processing the {0} system '
                'blob: {1}\nBad blob was:\n{2}'.format(
                    i, e.msg, e.bad_blob
                )
            }
        except ValidationError, e:
            transaction.rollback()
            field_errors = ''
            for field, errors in e.message_dict.iteritems():
                field_errors += "{0}: {1} ".format(field, ' '.join(errors))
            transaction.rollback()
            return None, {
                'errors': 'Found an issue while processing the {0} system '
                'blob: {1}\nBad blob was:\n{2}'.format(
                    i, field_errors, s_blob
                )
            }
        except Exception, e:
            transaction.rollback()
            return None, {
                'errors': 'Please tellsomeone about this error: {0}'
                'blob: {1}\nBad blob was:\n{2}'.format(i, str(e), s_blob)
            }
        else:
            transaction.commit()
            return {'systems': systems}, None

    return do_import()


def bulk_action_import(request):
    raw_data = request._get_raw_post_data()
    if not raw_data:
        return HttpResponse(dumps({'errors': 'what do you want?'}))
    systems, errors = bulk_import(raw_data)
    return HttpResponse(json.dumps(systems or errors))


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
    return HttpResponse(dumps({'systems': bundles}))
