from django.conf.urls.defaults import *
from django.views.decorators.csrf import csrf_exempt

from mozdns.soa.views import *

urlpatterns = patterns('',
    url(r'^$', SOAListView.as_view()),
    url(r'create/$', csrf_exempt(SOACreateView.as_view())),
    url(r'(?P<pk>[\w-]+)/update/$', csrf_exempt(SOAUpdateView.as_view())),
    url(r'(?P<pk>[\w-]+)/delete/$', csrf_exempt(SOADeleteView.as_view())),
    url(r'(?P<pk>[\w-]+)/$', csrf_exempt(SOADetailView.as_view())),
)
