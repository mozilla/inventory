from django.shortcuts import get_object_or_404
from django.shortcuts import render

from core.site.models import Site
from core.site.forms import SiteForm
from core.site.utils import get_vlans

from core.views import CoreDeleteView, CoreListView
from core.views import CoreCreateView, CoreUpdateView


class SiteView(object):
    model = Site
    queryset = Site.objects.all()
    form_class = SiteForm


class SiteDeleteView(SiteView, CoreDeleteView):
    success_url = '/core/site/'


def delete_site(request, site_pk):
    get_object_or_404(Site, pk=site_pk)
    if request.method == 'POST':
        return render(request, 'site/site_confirm_delete.html')

    else:
        return render(request, 'site/site_confirm_delete.html')


class SiteListView(SiteView, CoreListView):
    template_name = 'core/core_list.html'


class SiteCreateView(SiteView, CoreCreateView):
    template_name = 'core/core_form.html'


class SiteUpdateView(SiteView, CoreUpdateView):
    template_name = 'site/site_edit.html'


def site_detail(request, site_pk):
    from systems.models import SystemStatus
    # TODO, make this a top level import when SystemStatus is in it's own app
    site = get_object_or_404(Site, pk=site_pk)
    return render(request, 'site/site_detail.html', {
        'site': site,
        'vlans': get_vlans(site),
        'child_sites': site.site_set.all(),
        'attrs': site.keyvalue_set.all(),
        'statuses': SystemStatus.objects.all(),
    })
