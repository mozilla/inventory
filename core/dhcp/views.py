from core.dhcp.render import render_subnet
from core.network.models import Network
from django.shortcuts import get_object_or_404, render


def build_network(request, network_pk):
    network = get_object_or_404(Network, pk=network_pk)
    DEBUG_BUILD_STRING = render_subnet(network)
    return render(
        request, 'dhcp/sample_build.html', {'data': DEBUG_BUILD_STRING}
    )
