from django.core.exceptions import ObjectDoesNotExist

from mozdns.address_record.forms import AddressRecordForm
from mozdns.address_record.models import AddressRecord
from mozdns.domain.models import Domain
from mozdns.views import MozdnsDeleteView, MozdnsDetailView
from mozdns.views import MozdnsCreateView, MozdnsUpdateView, MozdnsListView
from core.network.utils import calc_parent_str

import pdb


class AddressRecordView(object):
    model = AddressRecord
    form_class = AddressRecordForm
    queryset = AddressRecord.objects.all()


class AddressRecordDeleteView(AddressRecordView, MozdnsDeleteView):
    """ """


class AddressRecordDetailView(AddressRecordView, MozdnsDetailView):
    def get_context_data(self, **kwargs):
        context = super(AddressRecordDetailView, self).get_context_data(
                **kwargs)
        context['form_title'] = "{0} Details".format(
            self.form_class.Meta.model.__name__
        )

        # extra_context takes precedence over original values in context
        if self.extra_context:
            context = dict(context.items() + self.extra_context.items())
        return context
    template_name = 'address_record/addressrecord_detail.html'


class AddressRecordCreateView(AddressRecordView, MozdnsCreateView):
    """ """
    def get_form(self, *args, **kwargs):
        initial = self.get_form_kwargs()
        if 'ip_type' in self.request.GET and 'ip_str' in self.request.GET:
            ip_str = self.request.GET['ip_str']
            ip_type = self.request.GET['ip_type']
            network = calc_parent_str(ip_str, ip_type)
            if network and network.vlan and network.site:
                expected_name = "{0}.{1}.mozilla.com".format(
                    network.vlan.name,
                    network.site.get_site_path())
                try:
                    domain = Domain.objects.get(name=expected_name)
                except ObjectDoesNotExist, e:
                    domain = None

            if domain:
                initial['initial'] = {'ip_str': ip_str, 'domain': domain,
                        'ip_type': ip_type}
            else:
                initial['initial'] = {'ip_str': ip_str, 'ip_type': ip_type}

        return AddressRecordForm(**initial)


class AddressRecordUpdateView(AddressRecordView, MozdnsUpdateView):
    """ """


class AddressRecordListView(AddressRecordView, MozdnsListView):
    """ """
