from django.shortcuts import render
from django.db.models import Q

from base.views import BaseListView, BaseDetailView, BaseCreateView
from base.views import BaseUpdateView, BaseDeleteView
from core.site.models import Site
from core.utils import to_a

import itertools


class CoreListView(BaseListView):
    """ """
    template_name = 'core/core_list.html'


class CoreDetailView(BaseDetailView):
    """ """
    template_name = 'core/core_detail.html'


class CoreCreateView(BaseCreateView):
    """ """
    template_name = 'core/core_form.html'


class CoreUpdateView(BaseUpdateView):
    """ """
    template_name = 'core/core_form.html'


class CoreDeleteView(BaseDeleteView):
    """ """
    template_name = 'core/core_confirm_delete.html'
    succcess_url = '/core/'


def core_index(request):
    sites = Site.objects.all()

    def width_helper(text):
        return len(text) * 8  # hackhackhack

    def get_security_zone(network):
        kv = network.keyvalue_set.filter(key='security_zone')
        if kv:
            return to_a(kv[0].value, kv[0])
        else:
            return ''

    table_meta_template = {
        'caption': '',
        'vlans': None,
        'sites': None,
        'headers': [
            ('name', lambda v: to_a(v.name, v)),
            ('number', lambda v: to_a(v.number, v))
        ],
        'network_data': [
            # This will be applied per network in a vlan and
            # wll be the stored in the td
            ('security_zone', get_security_zone),
            ('network', lambda n: to_a(n.network_str, n))
        ]
    }

    tables = []

    all_names = (
        Site.objects.order_by('name').values_list('name', flat=True).distinct()
    )

    def make_table(caption, sites):
        nets = []
        for site in sites:
            nets.append(
                site.network_set.filter(site=site).filter(~Q(vlan=None))
            )
        flat_nets = list(itertools.chain(*nets))

        vlans = set(map(lambda n: n.vlan, flat_nets))
        table = table_meta_template.copy()
        table['caption'] = caption
        table['vlans'] = vlans
        table['sites'] = sites
        return table

    for site_name in all_names:
        sites = Site.objects.filter(name=site_name)
        tables.append(make_table(site_name.title(), sites))

    return render(request, 'core/core_index.html', {
        'sites': sites,
        'tables': tables,
        'width_helper': width_helper
    })
