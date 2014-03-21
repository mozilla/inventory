from django.http import HttpResponse
from django.core.exceptions import ValidationError
from django.db import transaction

from decommission.decommission_utils import BadData, decommission_host

import MySQLdb

import simplejson as json

import reversion


def decommission_(main_blob, load_json=True):
    try:
        if load_json:
            json_blob = json.loads(main_blob)
        else:
            json_blob = main_blob
    except ValueError, e:  # Can't find JSONDecodeError
        return None, {'errors': str(e)}

    try:
        systems = json_blob['systems']
    except (KeyError, TypeError):
        return None, {'errors': 'Main JSON needs to have a key "systems".'}

    options = json_blob.get('options', {})
    opts = {
        'decommission_system_status': 'decommissioned',
        'decommission_sreg': True,
        'convert_to_sreg': True,
        'remove_dns': True
    }
    opts.update(options)

    commit = json_blob.get('commit', False)
    comment = json_blob.get('comment', '')

    if not isinstance(systems, list):
        return None, {'errors': 'Was expecting {"systems": [...]}'}

    @transaction.commit_manually
    def do_decommission():
        messages = []
        if reversion.revision_context_manager.is_active():
            reversion.set_comment(comment)
        try:
            for i, hostname in enumerate(systems):
                messages += decommission_host(hostname, opts, comment)
        except BadData, e:
            transaction.rollback()
            return None, {
                'errors': 'Found an issue while processing system with '
                'hostname {0}. {1}'.format(hostname, e.msg)
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
                'errors': 'Found an issue while processing system with '
                'hostname {0}. {1}'.format(hostname, field_errors)
            }
        except MySQLdb.Warning, e:
            transaction.rollback()
            return None, {
                'errors': 'Found an issue while processing system with '
                'hostname {0}. {1}'.format(hostname, e.message)
            }
        except Exception, e:
            transaction.rollback()
            return None, {
                'errors': 'Please tell someone about this error: {0}'.format(e),  # noqa
            }
        else:
            if commit:
                transaction.commit()
            else:
                transaction.rollback()
            json_blob['messages'] = messages
            return json_blob, None

    return do_decommission()


def decommission(request):
    raw_data = request.raw_post_data
    if not raw_data:
        return HttpResponse(json.dumps({'errors': 'what do you want?'}))
    systems, errors = decommission_(raw_data)
    return HttpResponse(
        json.dumps(systems or errors), status=400 if errors else 200
    )
