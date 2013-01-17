from django.conf.urls.defaults import patterns, url

from core.network.views import (NetworkListView, create_network,
        network_detail, update_network, NetworkDeleteView, delete_network_attr)


urlpatterns = patterns('',
                       url(r'^$', NetworkListView.as_view()),
                       url(r'^create/$', create_network),
                       url(r'^(?P<network_pk>[\w-]+)/$', network_detail),
                       url(r'^(?P<network_pk>[\w-]+)/update/$',
                           update_network),
                       url(r'^(?P<pk>[\w-]+)/delete/$',
                           NetworkDeleteView.as_view()),
                       url(r'^attr/(?P<attr_pk>[\w-]+)/delete/$',
                           delete_network_attr),
                       )
