from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from django.shortcuts import redirect
from django.shortcuts import render

from mozdns.views import MozdnsCreateView
from mozdns.views import MozdnsDeleteView
from mozdns.views import MozdnsDetailView
from mozdns.views import MozdnsListView
from mozdns.views import MozdnsUpdateView
from mozdns.ip.forms import IpForm
from mozdns.ptr.forms import PTRForm
from mozdns.ptr.models import PTR
from mozdns.domain.models import Domain
from core.network.utils import calc_parent_str


class PTRView(object):
    model = PTR
    form_class = PTRForm
    queryset = PTR.objects.all()


class PTRDeleteView(PTRView, MozdnsDeleteView):
    """ """


class PTRDetailView(PTRView, MozdnsDetailView):
    """ """
    template_name = "ptr/ptr_detail.html"


class PTRCreateView(PTRView, MozdnsCreateView):
    def get_form(self, *args, **kwargs):
        initial = self.get_form_kwargs()
        if 'ip_type' in self.request.GET and 'ip_str' in self.request.GET:
            ip_str = self.request.GET['ip_str']
            ip_type = self.request.GET['ip_type']
            network = calc_parent_str(ip_str, ip_type)
            if network and network.vlan and network.site:
                expected_name = "{0}.{1}.mozilla.com".format(network.vlan.name,
                    network.site.get_site_path())
                try:
                    domain = Domain.objects.get(name=expected_name)
                except ObjectDoesNotExist, e:
                    domain = None

            if domain:
                initial['initial'] = {'ip_str': ip_str, 'name':"."+domain.name, 'ip_type':ip_type}
            else:
                initial['initial'] = {'ip_str': ip_str, 'ip_type':ip_type}

        return PTRForm(**initial)


class PTRUpdateView(PTRView, MozdnsUpdateView):
    """ """


class PTRListView(PTRView, MozdnsListView):
    """ """
