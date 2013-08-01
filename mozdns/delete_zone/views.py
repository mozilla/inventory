import simplejson as json

from django.core.exceptions import ValidationError
from django.shortcuts import render
from django.http import HttpResponse
from django.db import transaction

from mozdns.utils import get_zones

from core.search.compiler.django_compile import compile_to_django
from core.task.models import Task


def delete_zone_helper(domain_name):
    if not domain_name:
        return {
            'success': False,
            'message': 'Which zone do you want to delete?'
        }
    if domain_name in ('mozilla.com', 'mozilla.net', 'mozilla.org',
                       'allizom.org'):
        raise ValidationError('Go home.')

    zone_objs = compile_to_django("zone=:{0}".format(domain_name))

    rdtypes = ('CNAME', 'MX', 'A', 'SRV', 'PTR', 'SSHFP', 'NS', 'TXT')
    for rdtype in rdtypes:
        zone_objs[0][rdtype].delete()

    soa = zone_objs[0]['SOA'][0]
    root_domain = soa.root_domain

    def maybe_delete_domain(d):
        domain_status = []
        for cd in d.domain_set.all():
            if cd.soa == soa:
                domain_status.append(maybe_delete_domain(cd))
            else:
                domain_status.append(False)

        if reduce(lambda x, y: x and y, domain_status, True):
            d.delete()
            return True
        else:
            d.soa = None
            d.save()
            return False

    maybe_delete_domain(root_domain)
    # XXX Replace this when Inventory has celery
    Task.schedule_zone_rebuild(soa)
    soa.delete()
    return {'success': True, 'message': 'success'}


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
