from django.conf.urls.defaults import *
from django.views.decorators.csrf import csrf_exempt

from mozdns.sshfp.views import *

urlpatterns = patterns('',
    url(r'^$', SSHFPListView.as_view()),
    url(r'(?P<domain>[\w-]+)/create/$', csrf_exempt(SSHFPCreateView.as_view())),
    url(r'create/$', csrf_exempt(SSHFPCreateView.as_view())),
    url(r'(?P<pk>[\w-]+)/update/$', csrf_exempt(SSHFPUpdateView.as_view())),
    url(r'(?P<pk>[\w-]+)/delete/$', csrf_exempt(SSHFPDeleteView.as_view())),
    url(r'(?P<pk>[\w-]+)/$', csrf_exempt(SSHFPDetailView.as_view())),
)
