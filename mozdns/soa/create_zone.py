import time
import simplejson as json
import pdb

from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, redirect
from django.http import HttpResponse
from mozdns.domain.models import Domain
from mozdns.nameserver.models import Nameserver
from mozdns.soa.models import SOA
from mozdns.utils import get_zones, ensure_domain
from gettext import gettext as _


def create_zone_ajax(request):
    """This view tries to creat a new zone and returns an JSON with either
    'success' = True or 'success' = False and some errors.
    """

    qd = request.POST.copy()
    # See if the domain exists.
    # Fail if it already exists or if it's under a delegated domain.
    root_domain = qd.get('root_domain', None)

    if not root_domain:
        error = "Please specify a root_domain"
        return HttpResponse(json.dumps({'success':False, 'error': error }))

    if Domain.objects.filter(name=root_domain).exists():
        error = _("<b>{0}</b> is already a domain. To make it a new zone, "
                  "assign it a newly created SOA.".format(root_domain))
        return HttpResponse(json.dumps({'success':False, 'error': error }))

    primary = qd.get('soa_primary', None)
    if not primary:
        error = "Please specify a primary nameserver for the SOA record."
    contact = qd.get('soa_contact', None)
    if not contact:
        error = "Please specify a contact address for the SOA record."
    contact.replace('@','.')

    # Find all the NS entries
    nss = []
    for k, v in request.POST.iteritems():
        if k.startswith('nameserver_'):
            ttl_key = qd.get('ttl_{0}'.format(v[-1:]))
            ttl = qd.get(ttl_key, 3600)
            server = v
            nss.append(Nameserver(server=server, ttl=ttl))

    # We want all domains created up to this point to inherit their
    # master_domain's soa. We will override the return domain's SOA.
    # Everything under this domain can be purgeable becase we will set this
    # domain to non-purgeable. This will also allow us to call prune tree.
    domain = ensure_domain(root_domain, purgeable=True, inherit_soa=False, force=True)

    soa = SOA(primary=primary, contact=contact, serial=int(time.time()))
    soa.save()
    domain.purgeable = False
    domain.soa = soa
    domain.save()
    for ns in nss:
        ns.domain = domain
        ns.save()

    return HttpResponse(json.dumps(
                {
                    'success':True,
                    'success_url': '/core/?search=zone=:{0}'.format(domain.name)
                }))

def create_zone(request):
    template_zone = request.GET.get('template_zone', '').strip('"')

    context = None
    message = ''
    if template_zone:
        try:
            root_domain = get_zones().get(name=template_zone)
            context = {
                'message': 'Using {0} as a template.'.format(template_zone),
                'root_domain': root_domain.name,
                'contact': root_domain.soa.contact,
                'primary': root_domain.soa.primary,
                'nss': root_domain.nameserver_set.all(),
            }
        except ObjectDoesNotExist:
            message = _('When trying to use {0} as a template, no zone '
                        'named {0} was found.'.format(template_zone))
    if not context:
        context = {
            'message': message,
            'root_domain': '',
            'contact': '',
            'primary': '',
            'nss': [],
        }

    return render(request, 'soa/zone_create.html', context)
