from django.conf.urls.defaults import *
from django.views.decorators.csrf import csrf_exempt

from mozdns.srv.views import *

urlpatterns = patterns('',
    url(r'^$', SRVListView.as_view()),
    url(r'(?P<domain>[\w-]+)/create/$', csrf_exempt(SRVCreateView.as_view())),
    url(r'create/$', csrf_exempt(SRVCreateView.as_view())),
    url(r'(?P<pk>[\w-]+)/update/$', csrf_exempt(SRVUpdateView.as_view())),
    url(r'(?P<pk>[\w-]+)/delete/$', csrf_exempt(SRVDeleteView.as_view())),
    url(r'(?P<pk>[\w-]+)/$', csrf_exempt(SRVDetailView.as_view())),
)
