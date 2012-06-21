from django.conf.urls.defaults import *
from django.views.decorators.csrf import csrf_exempt

from mozdns.mx.views import *

urlpatterns = patterns('',
    url(r'^$', MXListView.as_view() ),
    url(r'(?P<domain>[\w-]+)/create/$', csrf_exempt(MXCreateView.as_view())),
    url(r'create/$', csrf_exempt(MXCreateView.as_view())),
    url(r'(?P<pk>[\w-]+)/update/$', csrf_exempt(MXUpdateView.as_view() )),
    url(r'(?P<pk>[\w-]+)/delete/$', csrf_exempt(MXDeleteView.as_view() )),
    url(r'(?P<pk>[\w-]+)/$', csrf_exempt(MXDetailView.as_view() )),
)
