from django.conf.urls.defaults import *
from django.views.decorators.csrf import csrf_exempt

from mozdns.soa.views import *

urlpatterns = patterns('',
    url(r'^$', SOAListView.as_view()),
    url(r'attr/$', delete_soa_attr),
    url(r'create/$', csrf_exempt(SOACreateView.as_view())),
    url(r'(?P<soa_pk>[\w-]+)/update/$', csrf_exempt(update_soa)),
    url(r'(?P<pk>[\w-]+)/delete/$', csrf_exempt(SOADeleteView.as_view())),
    url(r'(?P<pk>[\w-]+)/$', csrf_exempt(SOADetailView.as_view())),
)
