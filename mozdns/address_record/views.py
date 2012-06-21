from django.core.exceptions import ObjectDoesNotExist

from mozdns.address_record.forms import AddressRecordForm
from mozdns.address_record.models import AddressRecord
from mozdns.views import MozdnsDeleteView, MozdnsDetailView
from mozdns.views import MozdnsCreateView, MozdnsUpdateView, MozdnsListView

import pdb

class AddressRecordView(object):
    model = AddressRecord
    form_class = AddressRecordForm
    queryset = AddressRecord.objects.all()


class AddressRecordDeleteView(AddressRecordView, MozdnsDeleteView):
    """ """


class AddressRecordDetailView(AddressRecordView, MozdnsDetailView):
    """ """
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


class AddressRecordUpdateView(AddressRecordView, MozdnsUpdateView):
    """ """


class AddressRecordListView(AddressRecordView, MozdnsListView):
    """ """
