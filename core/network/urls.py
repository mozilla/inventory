from django.conf.urls.defaults import patterns, url

from core.network.views import *


urlpatterns = patterns(
    '',
   url(r'^$', NetworkListView.as_view()),
   url(r'^create/$', NetworkCreateView.as_view()),
   url(r'^(?P<network_pk>[\w-]+)/$', network_detail),
   url(r'^(?P<pk>[\w-]+)/update/$', NetworkUpdateView.as_view()),
   url(r'^(?P<pk>[\w-]+)/delete/$', NetworkDeleteView.as_view()),
)
