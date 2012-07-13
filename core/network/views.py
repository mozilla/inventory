from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect
from django.shortcuts import render
from django.contrib import messages
from django.forms.util import ErrorList, ErrorDict
from django.http import HttpResponse

from core.network.models import Network, NetworkKeyValue
from core.network.forms import *
from core.network.utils import calc_networks, calc_parent_str
from core.vlan.models import Vlan
from core.site.models import Site
from core.site.forms import SiteForm
from core.keyvalue.utils import get_attrs, update_attrs, get_aa, get_docstrings
from core.keyvalue.utils import get_docstrings
from core.range.forms import RangeForm

from core.views import CoreDeleteView, CoreListView
from core.views import CoreCreateView
from mozdns.ip.models import ipv6_to_longs
from django.forms.formsets import formset_factory


import re
import pdb
import ipaddr
import simplejson as json

class NetworkView(object):
    model = Network
    queryset = Network.objects.select_related('site').all()
    form_class = NetworkForm

is_attr = re.compile("^attr_\d+$")

class NetworkDeleteView(NetworkView, CoreDeleteView):
    """ """

class NetworkListView(NetworkView, CoreListView):
    """ """
    template_name = 'network/network_list.html'

def delete_network_attr(request, attr_pk):
    """
    An view destined to be called by ajax to remove an attr.
    """
    attr = get_object_or_404(NetworkKeyValue, pk=attr_pk)
    attr.delete()
    return HttpResponse("Attribute Removed.")

def create_network(request):
    if request.method == 'POST':
        form = NetworkForm(request.POST)
        try:
            if form.is_valid():
                network = form.instance
                if network.site is None:
                    parent = calc_parent(network)
                    if parent:
                        network.site = parent.site
                network.save()
            return redirect(network)
        except ValidationError, e:
            return render(request, 'core/core_form.html', {
                'object': network,
                'form': form,
            })
    else:
        form = NetworkForm()
        return render(request, 'core/core_form.html', {
            'form': form,
        })


def update_network(request, network_pk):
    network = get_object_or_404(Network, pk=network_pk)
    attrs = network.networkkeyvalue_set.all()
    docs = get_docstrings(NetworkKeyValue())
    aa = get_aa(NetworkKeyValue())
    if request.method == 'POST':
        form = NetworkForm(request.POST, instance=network)
        try:
            if not form.is_valid():
                if form._errors is None:
                    form._errors = ErrorDict()
                form._errors['__all__'] = ErrorList(e.messages)
                return render(request, 'network/network_edit.html', {
                    'network': network,
                    'form': form,
                    'attrs': attrs,
                    'docs': docs,
                    'aa': json.dumps(aa)
                })
            else:
                # Handle key value stuff.
                kv = get_attrs(request.POST)
                update_attrs(kv, attrs, NetworkKeyValue, network, 'network')
                network = form.save()
                return redirect(network.get_edit_url())
        except ValidationError, e:
            if form._errors is None:
                form._errors = ErrorDict()
            form._errors['__all__'] = ErrorList(e.messages)
            return render(request, 'network/network_edit.html', {
                'network': network,
                'form': form,
                'attrs': attrs,
                'docs': docs,
                'aa': json.dumps(aa)
            })

    else:
        form = NetworkForm(instance=network)
        return render(request, 'network/network_edit.html', {
            'network': network,
            'form': form,
            'attrs': attrs,
            'docs': docs,
            'aa': json.dumps(aa)
        })

def network_detail(request, network_pk):
    network = get_object_or_404(Network, pk=network_pk)
    network.update_network()
    attrs = network.networkkeyvalue_set.all()
    eldars, sub_networks = calc_networks(network)
    ranges = network.range_set.all()
    return render(request, 'network/network_detail.html', {
        'network': network,
        'ranges': ranges,
        'eldars': eldars,
        'sub_networks': sub_networks,
        'attrs': attrs,
        })

