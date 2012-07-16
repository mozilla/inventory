from django.conf.urls.defaults import *
from django.views.decorators.csrf import csrf_exempt

from mozdns.ptr.views import *

urlpatterns = patterns('',
    url(r'^$', csrf_exempt(PTRListView.as_view())),
    url(r'create/$', csrf_exempt(PTRCreateView.as_view())),
    url(r'(?P<pk>[\w-]+)/update/$', csrf_exempt(PTRUpdateView.as_view())),
    url(r'(?P<pk>[\w-]+)/delete/$', csrf_exempt(PTRDeleteView.as_view())),
    url(r'(?P<pk>[\w-]+)/$', csrf_exempt(PTRDetailView.as_view())),
)
