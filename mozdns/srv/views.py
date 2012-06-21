from mozdns.views import MozdnsDeleteView
from mozdns.views import MozdnsCreateView
from mozdns.views import MozdnsDetailView
from mozdns.views import MozdnsUpdateView
from mozdns.views import MozdnsListView
from mozdns.srv.models import SRV
from mozdns.srv.forms import SRVForm


class SRVView(object):
    model = SRV
    form_class = SRVForm
    queryset = SRV.objects.all()


class SRVDeleteView(SRVView, MozdnsDeleteView):
    """SRV Delete View"""


class SRVDetailView(SRVView, MozdnsDetailView):
    """SRV Detail View"""
    template_name = 'srv/srv_detail.html'


class SRVCreateView(SRVView, MozdnsCreateView):
    """SRV Create View"""


class SRVUpdateView(SRVView, MozdnsUpdateView):
    """SRV Update View"""


class SRVListView(SRVView, MozdnsListView):
    """SRV List View"""
