from django.shortcuts import render

from base.base.views import BaseListView, BaseDetailView, BaseCreateView
from base.base.views import BaseUpdateView, BaseDeleteView
from core.vlan.models import Vlan
from core.site.models import Site
from core.utils import to_a


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
    vlans = Vlan.objects.all()
    sites = Site.objects.all()

    def width_helper(text):
        return len(text) * 8  # hackhackhack

    def get_security_zone(network):
        kv = network.keyvalue_set.filter(key='security_zone')
        if kv:
            return to_a(kv[0].value, kv[0])
        else:
            return ''

    table_meta = {
        'caption': 'The New Vlans Mana Page',
        'vlans': vlans,
        'headers': [
            ('name', lambda v: to_a(v.name, v)),
            ('number', lambda v: to_a(v.number, v))
        ],
        'network_data': [
            # This will be applied per network in a vlan and
            # wll be the stored in the td
            ('security_zone', get_security_zone),
            ('network', lambda n: to_a(n.network_str, n.site))
        ]
    }

    return render(request, 'core/core_index.html', {
        'sites': sites,
        'tables': [table_meta],
        'width_helper': width_helper
    })
