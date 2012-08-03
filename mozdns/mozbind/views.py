from mozdns.mozbind.build import *
from django.shortcuts import render_to_response, get_object_or_404
import simplejson as json

def build_forward_soa(request, soa_pk):
    soa = get_object_or_404(SOA, pk=soa_pk)
    DEBUG_BUILD_STRING = gen_moz_forward_zone(soa, NOWRITE=False)
    return render_to_response('mozbind/sample_build.html',
            {'data': DEBUG_BUILD_STRING, 'soa': soa})


def build_reverse_soa(request, soa_pk):
    soa = get_object_or_404(SOA, pk=soa_pk)
    DEBUG_BUILD_STRING = gen_moz_reverse_zone(soa, NOWRITE=False)
    return render_to_response('mozbind/sample_build.html',
            {'data': DEBUG_BUILD_STRING, 'soa': soa})

def build_soa(request, soa_pk):
    soa = get_object_or_404(SOA, pk=soa_pk)
    # Figure out what sort of domains are in this zone.
    domain_type = "forward"
    if soa.domain_set.all().exists():
        domain = soa.domain_set.all()[0]
        if domain.is_reverse:
            domain_type = "reverse"
        else:
            domain_type = "forward"
    try:
        stats = build_moz_zone(soa, domain_type, NOWRITE=False, request=request)
    except Exception, e:
        pdb.set_trace()
        return HttpResponse(json.dumps({"error": "HOLY SHIT SOMETHING WENT WRONG!!!"}))
    return HttpResponse(json.dumps(stats))
