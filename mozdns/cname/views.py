from mozdns.views import MozdnsDeleteView
from mozdns.views import MozdnsDetailView
from mozdns.views import MozdnsCreateView
from mozdns.views import MozdnsUpdateView
from mozdns.views import MozdnsListView
from mozdns.cname.models import CNAME
from mozdns.cname.forms import CNAMEForm


class CNAMEView(object):
    model = CNAME
    form_class = CNAMEForm
    queryset = CNAME.objects.all().order_by('fqdn')


class CNAMEDeleteView(CNAMEView, MozdnsDeleteView):
    """ """


class CNAMEDetailView(CNAMEView, MozdnsDetailView):
    """ """
    template_name = "cname/cname_detail.html"


class CNAMECreateView(CNAMEView, MozdnsCreateView):
    """ """


class CNAMEUpdateView(CNAMEView, MozdnsUpdateView):
    """ """


class CNAMEListView(CNAMEView, MozdnsListView):
    """ """
