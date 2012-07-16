from mozdns.mozbind.build import *
from django.shortcuts import render_to_response, get_object_or_404


def build_forward_soa(request, soa_pk):
    soa = get_object_or_404(SOA, pk=soa_pk)
    DEBUG_BUILD_STRING = gen_moz_forward_zone(soa, NOWRITE=True)
    return render_to_response('mozbind/sample_build.html',
            {'data': DEBUG_BUILD_STRING, 'soa': soa})


def build_reverse_soa(request, soa_pk):
    soa = get_object_or_404(SOA, pk=soa_pk)
    DEBUG_BUILD_STRING = gen_moz_reverse_zone(soa, NOWRITE=True)
    return render_to_response('mozbind/sample_build.html',
            {'data': DEBUG_BUILD_STRING, 'soa': soa})
