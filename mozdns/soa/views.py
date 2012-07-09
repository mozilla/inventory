from mozdns.domain.models import Domain
from mozdns.soa.forms import SOAForm
from mozdns.soa.models import SOA
from mozdns.utils import tablefy
from mozdns.views import MozdnsCreateView
from mozdns.views import MozdnsDeleteView
from mozdns.views import MozdnsDetailView
from mozdns.views import MozdnsListView
from mozdns.views import MozdnsUpdateView


class SOAView(object):
    model = SOA
    form_class = SOAForm
    queryset = SOA.objects.all()


class SOADeleteView(SOAView, MozdnsDeleteView):
    """ """


class SOADetailView(SOAView, MozdnsDetailView):
    """ """
    template_name = 'soa/soa_detail.html'

    def get_context_data(self, **kwargs):
        context = super(SOADetailView, self).get_context_data(**kwargs)
        soa = kwargs.get('object', False)
        if not soa:
            return soa

        dom_objects = soa.domain_set.all().order_by('master_domain').select_related()
        dom_headers, dom_matrix, dom_urls = tablefy(dom_objects)

        context = dict({
            "dom_headers": dom_headers,
            "dom_matrix": dom_matrix,
            "dom_urls": dom_urls,
        }.items() + context.items())

        return context


class SOACreateView(SOAView, MozdnsCreateView):
    """ """


class SOAUpdateView(SOAView, MozdnsUpdateView):
    """ """


class SOAListView(SOAView, MozdnsListView):
    """ """
