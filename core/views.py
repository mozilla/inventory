from base.mozdns.views import BaseListView, BaseDetailView, BaseCreateView
from base.mozdns.views import BaseUpdateView, BaseDeleteView


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

