from django.conf.urls.defaults import patterns, url

from core.dhcp.views import build_network

urlpatterns = patterns('',
    url(r'(?P<network_pk>[\w-]+)/$', build_network),
)
