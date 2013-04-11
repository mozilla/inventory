from base.base.views import BaseListView, BaseDetailView, BaseCreateView
from base.base.views import BaseUpdateView, BaseDeleteView

from django.forms.util import ErrorList
from django.core.exceptions import ObjectDoesNotExist, ValidationError

from core.forms import IpSearchForm
from core.network.models import Network
from core.network.utils import calc_networks, calc_parent
from mozdns.address_record.models import AddressRecord
from mozdns.ptr.models import PTR
from mozdns.ip.models import ipv6_to_longs

from django.shortcuts import render

import ipaddr


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


def search_ip(request):
    if request.method == "POST":
        form = IpSearchForm(request.POST)
        try:
            if form.is_valid():
                ip_type = form.cleaned_data['ip_type']
                search_ip = form.cleaned_data['search_ip']
                try:
                    if ip_type == '4':
                        network = ipaddr.IPv4Network(search_ip)
                    if ip_type == '6':
                        network = ipaddr.IPv6Network(search_ip)
                except ipaddr.AddressValueError, e:
                    form._errors['__all__'] = ErrorList(
                        ["Bad IPv{0} Address {1}".format(ip_type, search_ip)])
                    return render(request, 'core/core_form.html', {
                        'form': form
                    })
                try:
                    network = Network.objects.get(network_str=search_ip)
                    search_ip = network
                    found_exact = True
                except ObjectDoesNotExist:
                    found_exact = False
                    network = Network(ip_type, network_str=search_ip,
                                      ip_type=ip_type)
                parent = calc_parent(network)
                eldars, sub_networks = calc_networks(network)
                if ip_type == '6':
                    sip_upper, sip_lower = ipv6_to_longs(network.network.ip)
                    eip_upper, eip_lower = ipv6_to_longs(
                        network.network.broadcast)
                else:
                    sip_upper, sip_lower = 0, int(network.network.ip)
                    eip_upper, eip_lower = 0, int(network.network.broadcast)

                addrs_count = AddressRecord.objects.filter(
                    ip_upper__gte=sip_upper,
                    ip_lower__gte=sip_lower,
                    ip_upper__lte=eip_upper,
                    ip_lower__lte=eip_lower).count()

                if addrs_count > 100:
                    addrs = None  # This is too much
                else:
                    addrs = AddressRecord.objects.filter(
                        ip_upper__gte=sip_upper,
                        ip_lower__gte=sip_lower,
                        ip_upper__lte=eip_upper,
                        ip_lower__lte=eip_lower)

                ptrs_count = PTR.objects.filter(
                    ip_upper__gte=sip_upper,
                    ip_lower__gte=sip_lower,
                    ip_upper__lte=eip_upper,
                    ip_lower__lte=eip_lower).count()

                if ptrs_count > 100:
                    ptrs = None  # This is too much
                else:
                    ptrs = PTR.objects.filter(
                        ip_upper__gte=sip_upper,
                        ip_lower__gte=sip_lower,
                        ip_upper__lte=eip_upper,
                        ip_lower__lte=eip_lower)

            return render(request, 'core/core_results.html', {
                'search_ip': search_ip,
                'found_exact': found_exact,
                'addrs': addrs,
                'addrs_count': addrs_count,
                'ptrs_count': ptrs_count,
                'ptrs': ptrs,
                'parent': parent,
                'eldars': eldars,
                'sub_networks': sub_networks,
            })
        except ValidationError, e:
            form._errors['__all__'] = ErrorList(e.messages)
            return render(request, 'core/core_form.html', {
                'form': form
            })
    else:
        form = IpSearchForm()
        return render(request, 'core/core_form.html', {
            'form': form
        })
