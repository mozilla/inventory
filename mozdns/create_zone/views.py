import simplejson as json
import re

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.shortcuts import render
from django.http import HttpResponse
from django.db import transaction

from mozdns.nameserver.models import Nameserver
from mozdns.soa.models import SOA
from mozdns.view.models import View
from mozdns.utils import get_zones, ensure_domain, prune_tree


def _create_zone(root_domain, primary, contact, nss):
    if not root_domain:
        raise ValueError("Please specify a root_domain")

    if not primary:
        raise ValueError(
            "Please specify a primary nameserver for the SOA record."
        )

    if not contact:
        raise ValueError(
            "Please specify a contact address for the SOA record."
        )
    contact.replace('@', '.')

    if not nss:
        # They must create at least one nameserver
        raise ValueError(
            "You must choose an authoritative nameserver to serve this "
            "zone."
        )

    try:
        soa = SOA.objects.create(
            primary=primary, contact=contact,
            description="SOA for {0}".format(root_domain)
        )
    except ValidationError, e:
        # Make how the error is being stored a little more friendly.
        raise ValidationError(e.messages[0])

    # We want all domains created up to this point to inherit their
    # master_domain's soa so we will say inherit_soa=False and then override
    # the return domain's SOA.
    # Everything under this domain can be purgeable becase we will set this
    # domain to non-purgeable. This will also allow us to call prune tree.
    domain = ensure_domain(
        root_domain, purgeable=False, inherit_soa=False, force=True
    )
    _save_nss(nss, domain)
    domain.soa = soa
    # ensure_domain doesn't ensure it created the domain with purgeable equal
    # to True.
    domain.purgeable = False
    domain.save()
    return domain


def _save_nss(nss, domain):
    # Helper function for saving the nameserver bits in the create_zone form
    private_view, _ = View.objects.get_or_create(name='private')
    public_view, _ = View.objects.get_or_create(name='public')

    for i, (server, ttl, views) in enumerate(nss):
        try:
            ns, _ = Nameserver.objects.get_or_create(
                domain=domain, ttl=ttl, server=server
            )
            if 'public' in views:
                ns.views.add(public_view)
            if 'private' in views:
                ns.views.add(private_view)
            ns.save()
        except ValidationError, e:
            suffixes = ["th", "st", "nd", "rd", ] + ["th"] * 16
            suffixed_i = str(i + 1) + suffixes[i + 1 % 100]
            error_field, error_val = e.message_dict.items()[0]
            raise ValidationError(
                "When trying to create the {0} nameserver entry, the "
                "nameserver field '{1}' returned the error "
                "'{2}'".format(suffixed_i, error_field, error_val[0])
            )


def create_zone_ajax(request):
    """
    This view tries to create a new zone and returns an JSON with either
    'success' = True or 'success' = False and some errors.
    """

    qd = request.POST.copy()
    # See if the domain exists.
    # Fail if it already exists or if it's under a delegated domain.
    root_domain = qd.get('root_domain', None)
    primary = qd.get('soa_primary', None)
    contact = qd.get('soa_contact', None)

    # Find all the NS entries
    nss = []
    number_re = re.compile('nameserver_(\d+)')
    # parse nameserver bits from POST request.
    # compile some tuples that look like:
    #   (<server_fqdn>, <ttl>, [<view_name>,..])
    for k, server in request.POST.iteritems():
        if k.startswith('nameserver_'):
            n = number_re.search(k)
            if not n:
                continue
            ns_number = n.groups()[0]
            views = []
            if qd.get('private_view_{0}'.format(ns_number), 'off') == 'on':
                views.append('private')
            if qd.get('public_view_{0}'.format(ns_number), 'off') == 'on':
                views.append('public')
            ttl = qd.get('ttl_{0}'.format(ns_number))
            if ttl and ttl.isdigit():
                ttl = int(ttl)
            else:
                ttl = None
            nss.append(
                (server, ttl, views)
            )

    try:
        with transaction.commit_on_success():
            domain = _create_zone(root_domain, primary, contact, nss)
    except (ValueError, ValidationError), e:
        return HttpResponse(json.dumps({
            'success': False, 'error': str(e)
        }), status=400)

    return HttpResponse(json.dumps({
        'success': True,
        'success_url': '/en-US/core/search/#q=zone=:{0}'.format(
            domain.name
        )
    }))


def _clean_domain_tree(domain):
    if not domain.master_domain:
        # They tried to create a TLD, prune_tree will not delete it.
        domain.delete()
    else:
        domain.purgeable = True
        prune_tree(domain)  # prune_tree will delete this domain


def create_zone(request):
    template_zone = request.GET.get('template_zone', '').strip('"')

    context = None
    message = ''
    zones = get_zones()
    if template_zone:
        try:
            root_domain = zones.get(name=template_zone)
            context = {
                'message': 'Using {0} as a template.'.format(template_zone),
                'root_domain': root_domain.name,
                'contact': root_domain.soa.contact,
                'primary': root_domain.soa.primary,
                'nss': root_domain.nameserver_set.all(),
                'zones': json.dumps(
                    sorted([z.name for z in get_zones()], reverse=True))
            }
        except ObjectDoesNotExist:
            message = (
                "When trying to use {0} as a template, no zone "
                "named {0} was found.".format(template_zone)
            )
    if not context:
        context = {
            'message': message,
            'root_domain': '',
            'contact': '',
            'primary': '',
            'nss': [],
            'zones': json.dumps(
                sorted([z.name for z in get_zones()], reverse=True))
        }

    return render(request, 'create_zone/create_zone.html', context)
