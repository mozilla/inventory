# Create your views here.
from mozdns.views import MozdnsDeleteView
from mozdns.views import MozdnsCreateView
from mozdns.views import MozdnsDetailView
from mozdns.views import MozdnsUpdateView
from mozdns.views import MozdnsListView
from mozdns.txt.models import TXT
from mozdns.txt.forms import TXTForm


class TXTView(object):
    model = TXT
    form_class = TXTForm
    queryset = TXT.objects.all()


class TXTDeleteView(TXTView, MozdnsDeleteView):
    """ """


class TXTDetailView(TXTView, MozdnsDetailView):
    """ """
    template_name = 'txt/txt_detail.html'


class TXTCreateView(TXTView, MozdnsCreateView):
    """ """


class TXTUpdateView(TXTView, MozdnsUpdateView):
    """ """


class TXTListView(TXTView, MozdnsListView):
    """ """
