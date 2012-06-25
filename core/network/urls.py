from django.conf.urls.defaults import *

from core.network.views import *

urlpatterns = patterns('',
    url(r'^$', NetworkListView.as_view()),
    url(r'^create/$', create_network),
    url(r'^(?P<network_pk>[\w-]+)/$', network_detail),
    url(r'^(?P<network_pk>[\w-]+)/update/$', update_network),
    url(r'^(?P<pk>[\w-]+)/delete/$', NetworkDeleteView.as_view()),

)
