import simplejson as json

from django.core.exceptions import ValidationError
from django.shortcuts import render
from django.http import HttpResponse
from django.db import transaction

from mozdns.utils import get_zones

from mozdns.delete_zone.utils import delete_zone_helper


def delete_zone_ajax(request):
    domain_name = request.POST.get('domain_name', '')

    @transaction.commit_manually
    def delete_zone():
        try:
            return delete_zone_helper(domain_name)
        except ValidationError, e:
            transaction.rollback()
            return {'success': False, 'message': e.messages}
        except Exception, e:
            transaction.rollback()
            return {'success': False, 'message': ['Error: ' + e.message]}
        finally:
            transaction.commit()

    return HttpResponse(json.dumps(delete_zone()))


def delete_zone(request):
    domain_name = request.GET.get('domain_name', '')
    zones = get_zones().values_list('name', flat=True)
    return render(request, 'delete_zone/delete_zone.html', {
        'domain_name': domain_name,
        'zones': json.dumps(list(zones))
    })
