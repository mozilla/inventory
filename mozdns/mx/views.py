from mozdns.mx.models import MX
from mozdns.mx.forms import MXForm
from mozdns.views import MozdnsDeleteView
from mozdns.views import MozdnsDetailView
from mozdns.views import MozdnsCreateView
from mozdns.views import MozdnsListView
from mozdns.views import MozdnsUpdateView


class MXView(object):
    """Group together common attributes."""
    model = MX
    form_class = MXForm
    queryset = MX.objects.all()


class MXDeleteView(MXView, MozdnsDeleteView):
    """ """


class MXDetailView(MXView, MozdnsDetailView):
    """ """
    template_name = 'mx/mx_detail.html'


class MXCreateView(MXView, MozdnsCreateView):
    """ """


class MXUpdateView(MXView, MozdnsUpdateView):
    """ """


class MXListView(MXView, MozdnsListView):
    """ """
