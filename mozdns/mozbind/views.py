from mozdns.mozbind.build import *
from django.shortcuts import render_to_response, get_object_or_404
import simplejson as json

def build_debug_soa(request, soa_pk):
    soa = get_object_or_404(SOA, pk=soa_pk)
    root_domain = find_root_domain(soa)
    if not root_domain:
        DEBUG_BUILD_STRING = ";No data in this zone"
    else:
        if root_domain.is_reverse:
            zone_type = "reverse"
        else:
            zone_type = "forward"
        _, _, DEBUG_BUILD_STRING = build_zone(zone_type, soa, root_domain)
    return render_to_response('mozbind/sample_build.html',
            {'data': DEBUG_BUILD_STRING, 'soa': soa})

def build_soa(request, soa_pk):
    soa = get_object_or_404(SOA, pk=soa_pk)
    root_domain = find_root_domain(soa)
    DEBUG_BUILD_STRING = build_zone(soa, root_domain)
    # Figure out what sort of domains are in this zone.
    if root_domain.is_reverse:
        domain_type = "reverse"
    else:
        domain_type = "forward"
    try:
        stats = build_moz_zone(soa, domain_type, NOWRITE=False, request=request)
    except Exception, e:
        pdb.set_trace()
        return HttpResponse(json.dumps({"error": "HOLY SHIT SOMETHING WENT WRONG!!!"}))
    return HttpResponse(json.dumps(stats))
