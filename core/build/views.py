from core.build.subnet import build_subnet
from core.network.models import Network
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse

import pdb


def build_network(request, network_pk):
    network = get_object_or_404(Network, pk=network_pk)
    if request.GET.pop("raw", False):
        DEBUG_BUILD_STRING = build_subnet(network, raw=True)
        return HttpResponse(DEBUG_BUILD_STRING)
    else:
        DEBUG_BUILD_STRING = build_subnet(network, raw=False)
        return render_to_response('build/sample_build.html',
                {'data': DEBUG_BUILD_STRING, 'network': network})
