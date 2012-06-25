from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.shortcuts import render
from django.contrib import messages
from django.forms.util import ErrorList, ErrorDict
from django.http import HttpResponse

from core.site.models import Site, SiteKeyValue
from core.site.forms import SiteForm
from core.site.utils import get_vlans

from core.vlan.models import Vlan
from core.network.models import Network
from core.keyvalue.utils import get_attrs, update_attrs

from core.views import CoreDeleteView, CoreListView
from core.views import CoreCreateView, CoreUpdateView



import re
import pdb
import ipaddr

class SiteView(object):
    model = Site
    queryset = Site.objects.all()
    form_class = SiteForm

is_attr = re.compile("^attr_\d+$")

class SiteDeleteView(SiteView, CoreDeleteView):
    success_url = '/core/site/'

class SiteListView(SiteView, CoreListView):
    """ """
    template_name = 'core/core_list.html'

class SiteCreateView(SiteView, CoreCreateView):
    """ """
    template_name = 'core/core_form.html'

class SiteUpdateView(SiteView, CoreUpdateView):
    """ """
    template_name = 'site/site_edit.html'


def update_site(request, site_pk):
    site = get_object_or_404(Site, pk=site_pk)
    attrs = site.sitekeyvalue_set.all()
    aux_attrs = SiteKeyValue.aux_attrs
    if request.method == 'POST':
        form = SiteForm(request.POST, instance=site)
        try:
            # Handle KV store.
            kv = get_attrs(request.POST)
            update_attrs(kv, attrs, SiteKeyValue, site, 'site')

            # Do site stuff.
            networks = form.data.getlist('networks')
            cur_networks = site.network_set.all()
            new_networks = []
            for n_pk in networks:
                n = get_object_or_404(Network, pk=n_pk)
                new_networks.append(n)
                if n in cur_networks:
                    continue
                else:
                    n.sites.add(site)
                    n.save()
            for n in cur_networks:
                if n not in new_networks:
                    n.sites.remove(site)
                    n.save()
            return redirect(site)
        except ValidationError, e:
            if form._errors is None:
                form._errors = ErrorDict()
            form._errors['__all__'] = ErrorList(e.messages)
            return render(request, 'site/site_edit.html', {
                'site': site,
                'form': form,
                'attrs': attrs,
                'aux_attrs': aux_attrs
            })

    else:
        form = SiteForm(instance=site)
        form.fields['networks'].initial = site.network_set.all()
        return render(request, 'site/site_edit.html', {
            'site': site,
            'form': form,
            'attrs': attrs,
            'aux_attrs': aux_attrs
        })

def site_detail(request, site_pk):
    site = get_object_or_404(Site, pk=site_pk)
    attrs = site.sitekeyvalue_set.all()
    vlans = get_vlans(site)
    if request.method == 'POST':
        pass
    else:
        return render(request, 'site/site_detail.html', {
            'site': site,
            'vlans': vlans,
            'attrs': attrs
        })
