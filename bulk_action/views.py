from django.http import HttpResponse
from django.core.exceptions import ValidationError
from django.db import transaction

from systems.models import System

from core.range.utils import range_usage
from core.search.compiler.django_compile import compile_to_q
from core.range.ip_choosing_utils import (
    integrate_real_ranges, calc_template_ranges
)
from core.network.models import Network

from bulk_action.import_utils import loads, dumps, system_import, BadImportData

from MySQLdb import OperationalError
import MySQLdb

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

    commit = json_blob.get('commit', False)

    if not isinstance(systems, dict):
        return None, {'errors': 'Main JSON blob must be a dict of systems'}

    @transaction.commit_manually
    def do_import():
        try:
            for i, s_blob in enumerate(systems.values()):
                save_functions = sorted(
                    system_import(s_blob), key=lambda f: f[0]
                )
                for priority, fn in save_functions:
                    fn()
        except BadImportData, e:
            transaction.rollback()
            return None, {
                'errors': 'Found an issue while processing system #{0}'
                'blob: {1}\nBad blob was:\n{2}'.format(
                    i, e.msg, e.bad_blob
                )
            }
        except ValidationError, e:
            transaction.rollback()
            field_errors = ''
            if hasattr(e, 'message_dict'):
                for field, errors in e.message_dict.iteritems():
                    field_errors += "{0}: {1} ".format(field, ' '.join(errors))
            else:
                field_errors = ', '.join(e.messages)
            transaction.rollback()
            return None, {
                'errors': 'Found an issue while processing system #{0}: '
                '{field_errors}'.format(i, field_errors=field_errors),  # noqa
                'blob': s_blob,
                'blob_number': i
            }
        except MySQLdb.Warning, e:
            transaction.rollback()
            return None, {
                'errors': (
                    'There was an error while processing system number #{0}: '
                    '{error}.'.format(i, error=e.message)
                ),
                'blob': s_blob,
                'blob_number': i
            }
        except Exception, e:
            transaction.rollback()
            return None, {
                'errors': 'Please tell someone about this error: {0}'.format(e),  # noqa
                'blob': s_blob,
                'blob_number': i
            }
        else:
            if commit:
                transaction.commit()
            else:
                transaction.rollback()
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


def bulk_gather_vlan_pools(request):
    vlan_name = request.GET.get('vlan_name', None)
    vlan_number = request.GET.get('vlan_number', None)
    site_name = request.GET.get('site_name', None)
    ip_type = request.GET.get('ip_type', None)

    if not site_name:
        return HttpResponse(dumps({
            'errors': 'Site name was not provided'
        }))

    if not ip_type:
        return HttpResponse(dumps({
            'errors': 'IP type is required here.'
        }))

    if vlan_name and vlan_number:
        s = 'site=:{site_name} AND vlan=:{vlan_name},{vlan_number}'.format(
            site_name=site_name, vlan_name=vlan_name, vlan_number=vlan_number
        )
    elif vlan_name:
        s = 'site=:{site_name} AND vlan=:{vlan_name}'.format(
            site_name=site_name, vlan_name=vlan_name
        )
    elif vlan_number:
        s = 'site=:{site_name} AND vlan=:{vlan_number}'.format(
            site_name=site_name, vlan_number=vlan_number
        )
    else:
        return HttpResponse(dumps({
            'errors': 'Not enough vlan information was provided'
        }))

    q_map, errors = compile_to_q(s)

    if errors:
        return None, errors

    networks = Network.objects.filter(q_map['NET']).filter(ip_type=ip_type)
    if networks.count() > 1:
        return HttpResponse(dumps({
            'errors': "Using the search '{s}', too many networks were "
            "found. Please be more specific and specify a range.".format(s=s)
        }))
    if not networks.count():
        return HttpResponse(dumps({
            'errors': "Using the search '{s}', no networks were "
            "found.".format(s=s)
        }))

    ranges = integrate_real_ranges(
        networks[0], calc_template_ranges(networks[0])
    )
    free_ranges = []
    for r in ranges:
        if r['rtype'] == 'special purpose':
            continue
        free_ranges += range_usage(
            r['start'], r['end'], ip_type
        )['free_ranges']

    return HttpResponse(dumps({
        'free_ranges': free_ranges
    }))
