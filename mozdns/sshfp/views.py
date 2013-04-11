# Create your views here.
from mozdns.views import MozdnsDeleteView
from mozdns.views import MozdnsCreateView
from mozdns.views import MozdnsDetailView
from mozdns.views import MozdnsUpdateView
from mozdns.views import MozdnsListView
from mozdns.sshfp.models import SSHFP
from mozdns.sshfp.forms import SSHFPForm


class SSHFPView(object):
    model = SSHFP
    form_class = SSHFPForm
    queryset = SSHFP.objects.all()


class SSHFPDeleteView(SSHFPView, MozdnsDeleteView):
    """ """


class SSHFPDetailView(SSHFPView, MozdnsDetailView):
    """ """
    template_name = 'sshfp/sshfp_detail.html'


class SSHFPCreateView(SSHFPView, MozdnsCreateView):
    """ """


class SSHFPUpdateView(SSHFPView, MozdnsUpdateView):
    """ """


class SSHFPListView(SSHFPView, MozdnsListView):
    """ """
