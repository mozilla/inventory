from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect
from django.shortcuts import render
from django.contrib import messages
from django.forms.util import ErrorList, ErrorDict
from django.http import HttpResponse

from core.network.models import Network, NetworkKeyValue
from core.network.forms import NetworkForm
from core.network.utils import calc_networks, calc_parent
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
def create_network(request):
    if request.method == 'POST':
        form = NetworkForm(request.POST, instance=network)
    else:
        form = NetworkForm(request.POST)

def update_network(request, network_pk):
    network = get_object_or_404(Network, pk=network_pk)
    attrs = network.networkkeyvalue_set.all()
    aux_attrs = NetworkKeyValue.aux_attrs
    if request.method == 'POST':
        form = NetworkForm(request.POST, instance=network)
        try:
            if form.is_valid():
                # Handle key value stuff.
                kv = get_attrs(request.POST)
                update_attrs(kv, attrs, NetworkKeyValue, network, 'network')

                network = form.instance
                sites = form.data.getlist('sites')
                vlan = form.data.get('vlan')
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
                        # If any of our children are relying on us to be in this
                        # site, back out.
                        eldars, sub_networks = calc_networks(network)
                        for sub_network in sub_networks:
                            if site in sub_network.sites.all():
                                raise ValidationError("Network {0} is in Site {1}."
                                    "Remove {0} from {1} before removing this "
                                    "Network from {1}".format(sub_network, site))
                            else:
                                network.sites.remove(site)
                try:
                    network.save()
                except IntegrityError, e:
                    raise ValidationError("Network {0} already "
                            "exists.".format(network))
            return redirect(network)
        except ValidationError, e:
            form = NetworkForm(instance=network)
            if form._errors is None:
                form._errors = ErrorDict()
            form._errors['__all__'] = ErrorList(e.messages)
            return render(request, 'network/network_edit.html', {
                'network': network,
                'form': form,
                'attrs': attrs,
                'aux_attrs': aux_attrs
            })

    else:
        form = NetworkForm(instance=network)
        form.fields['sites'].initial = network.sites.all()
        return render(request, 'network/network_edit.html', {
            'network': network,
            'form': form,
            'attrs': attrs,
            'aux_attrs': aux_attrs
        })


def network_detail(request, network_pk):
    network = get_object_or_404(Network, pk=network_pk)
    network.update_network()
    attrs = network.networkkeyvalue_set.all()
    eldars, sub_networks = calc_networks(network)
    return render(request, 'network/network_detail.html', {
        'network': network,
        'eldars': eldars,
        'sub_networks': sub_networks,
        'attrs': attrs
    })
