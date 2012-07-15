from core.build.subnet import build_subnet
from core.network.models import Network
from django.shortcuts import render_to_response, get_object_or_404

import pdb

def build_network(request, network_pk):
    network = get_object_or_404(Network, pk=network_pk)
    DEBUG_BUILD_STRING = build_subnet(network)
    return render_to_response('build/sample_build.html',
            {'data':DEBUG_BUILD_STRING, 'network':network})
