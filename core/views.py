from mozdns.base.views import BaseListView, BaseDetailView, BaseCreateView
from mozdns.base.views import BaseUpdateView, BaseDeleteView


class CoreDeleteView(BaseDeleteView):
    """ """
    template_name = "core/core_confirm_delete.html"


class CoreDetailView(BaseDetailView):
    """ """
    template_name = "core/core_detail.html"


class CoreCreateView(BaseCreateView):
    """ """
    template_name = "core/core_form.html"


class CoreUpdateView(BaseUpdateView):
    """ """
    template_name = "core/core_form.html"


class CoreListView(BaseListView):
    """ """
    template_name = 'core/core_list.html'
