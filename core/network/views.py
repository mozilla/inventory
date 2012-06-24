from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.shortcuts import render
from django.contrib import messages
from django.forms.util import ErrorList
from django.http import HttpResponse

from core.network.models import Network, NetworkKeyValue
from core.network.forms import NetworkForm
from core.vlan.models import Vlan
from core.site.models import Site
from core.keyvalue.utils import get_attrs, update_attrs

from core.views import CoreDeleteView, CoreListView
from core.views import CoreCreateView


import re
import pdb
import ipaddr

class NetworkView(object):
    model = Network
    queryset = Network.objects.all()
    form_class = NetworkForm

is_attr = re.compile("^attr_\d+$")

class NetworkDeleteView(NetworkView, CoreDeleteView):
    """ """

class NetworkListView(NetworkView, CoreListView):
    """ """
    template_name = 'core/core_list.html'

class NetworkCreateView(NetworkView, CoreCreateView):
    """ """
    template_name = 'core/core_form.html'

def update_network(request, network_pk):
    network = get_object_or_404(Network, pk=network_pk)
    attrs = network.networkkeyvalue_set.all()
    if request.method == 'POST':
        form = NetworkForm(request.POST, instance=network)
        try:
            # Handle key value stuff.
            kv = get_attrs(request.POST)
            update_attrs(kv, attrs, NetworkKeyValue, network, 'network')

            network = form.save()
            sites = form.data.getlist('sites')
            cur_sites = network.sites.all()
            new_sites = []
            # Handle new ones.
            for site_pk in sites:
                site = get_object_or_404(Site, pk=site_pk)
                new_sites.append(site)
                if site in cur_sites:
                    continue
                else:
                    network.sites.add(site)
                    network.save()
            for site in cur_sites:
                if site not in new_sites:
                    network.sites.remove(site)
                    network.save()
            return redirect(network)
        except ValidationError, e:
            if form._errors is None:
                form._errors = ErrorDict()
            form._errors['__all__'] = ErrorList(e.messages)
            return render(request, 'network/network_edit.html', {
                'network': network,
                'form': form,
                'attrs': attrs
            })

    else:
        form = NetworkForm(instance=network)
        form.fields['sites'].initial = network.sites.all()
        return render(request, 'network/network_edit.html', {
            'network': network,
            'form': form,
            'attrs': attrs
        })

def network_detail(request, network_pk):
    network = get_object_or_404(Network, pk=network_pk)
    network.update_network()
    attrs = network.networkkeyvalue_set.all()
    eldars = []
    sub_networks = []
    for pnet in Network.objects.all():
        pnet.update_network()
        if pnet.pk == network.pk:
            continue
        if pnet.network.overlaps(network.network):
            if pnet.prefixlen > network.prefixlen:
                sub_networks.append(pnet)
            else:
                eldars.append(pnet)

    return render(request, 'network/network_detail.html', {
        'network': network,
        'eldars': eldars,
        'sub_networks': sub_networks,
        'attrs': attrs
    })
