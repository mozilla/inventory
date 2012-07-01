# Create your views here.
from mozdns.views import MozdnsDeleteView
from mozdns.views import MozdnsCreateView
from mozdns.views import MozdnsDetailView
from mozdns.views import MozdnsUpdateView
from mozdns.views import MozdnsListView
from mozdns.view.models import View
from mozdns.view.forms import ViewForm


class ViewView(object):
    model = View
    form_class = ViewForm
    queryset = View.objects.all()


class ViewDeleteView(ViewView, MozdnsDeleteView):
    """ """


class ViewDetailView(ViewView, MozdnsDetailView):
    """ """
    template_name = 'view/view_detail.html'


class ViewCreateView(ViewView, MozdnsCreateView):
    """ """


class ViewUpdateView(ViewView, MozdnsUpdateView):
    """ """


class ViewListView(ViewView, MozdnsListView):
    """ """
