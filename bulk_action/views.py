from django.http import HttpResponse

from systems.models import System

from core.search.compiler.django_compile import compile_to_q

from MySQLdb import OperationalError

import decimal
import datetime
import simplejson as json
import pprint


class BadImport(Exception):
    def __init__(self, bad_data=None, msg=''):
        self.bad_data = bad_data
        self.msg = msg
        return super(BadImportData).__init__()


class BAEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return str(o)
        elif isinstance(o, datetime.datetime) or isinstance(o, datetime.date):
            return o.isoformat()
        super(BAEncoder, self).default(o)


class BADecoder(json.JSONDecoder):
    pass


def dumps(j):
    return json.dumps(j, cls=BAEncoder)


def loads(j):
    return json.loads(j, cls=BADecoder)


def bulk_import(raw_data):
    try:
        data = loads(raw_data)
    except ValueError, e:  # Can't find JSONDecodeError
        return HttpResponse(dumps({'errors': str(e)}))
    if not isinstance(data, list):
        return HttpResponse(
            dumps({'errors': 'Data must be a list of systems'})
        )
    for s_data in data:
        system_import(s_data)
    print data
    return {}


def system_import(data):
    if 'pk' in data:
        try:
            system_update(data)
        except System.DoesNotExist:
            raise BadImport(
                bad_data=data,
                msg='Could not find the system corresponding to this data.'
            )


def system_update(data):
    pass


def bulk_action_import(request):
    data = request.POST.get('data', None)
    if not data:
        return HttpResponse(dumps({'errors': 'what do you want?'}))
    return HttpResponse(bulk_import(data))


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
