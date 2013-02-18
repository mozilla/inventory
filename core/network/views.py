from django.shortcuts import get_object_or_404
from django.shortcuts import render

from core.network.models import Network
from core.network.utils import calc_networks
from core.network.forms import NetworkForm

from core.views import (CoreDeleteView, CoreListView, CoreUpdateView,
                        CoreCreateView)


class NetworkView(object):
    model = Network
    queryset = Network.objects.select_related('site').all()
    form_class = NetworkForm


class NetworkDeleteView(NetworkView, CoreDeleteView):
    pass


class NetworkListView(NetworkView, CoreListView):
    template_name = 'network/network_list.html'


class NetworkUpdateView(NetworkView, CoreUpdateView):
    template_name = 'network/network_edit.html'


class NetworkCreateView(NetworkView, CoreCreateView):
    pass


def network_detail(request, network_pk):
    network = get_object_or_404(Network, pk=network_pk)
    network.update_network()
    attrs = network.keyvalue_set.all()
    eldars, sub_networks = calc_networks(network)
    ranges = network.range_set.all()
    return render(request, 'network/network_detail.html', {
        'network': network,
        'ranges': ranges,
        'eldars': eldars,
        'sub_networks': sub_networks,
        'attrs': attrs,
    })
