from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.shortcuts import render
from django.contrib import messages
from django.forms.util import ErrorList
from django.http import HttpResponse

from core.site.models import Site
from core.site.forms import SiteForm
from core.vlan.models import Vlan
from core.network.models import Network

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
    """ """

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
    if request.method == 'POST':
        form = SiteForm(request.POST, instance=site)
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

    else:
        form = SiteForm(instance=site)
        form.fields['networks'].initial = site.network_set.all()
        return render(request, 'site/site_edit.html', {
            'site': site,
            'form': form
        })

def site_detail(request, site_pk):
    site = get_object_or_404(Site, pk=site_pk)
    if request.method == 'POST':
        pass
    else:
        return render(request, 'site/site_detail.html', {
            'site': site
        })
