from django.conf.urls.defaults import patterns, url

from core.group.views import *

urlpatterns = patterns('',
   url(r'^$', GroupListView.as_view()),
   url(r'^create/$', GroupCreateView.as_view()),
   url(r'^(?P<group_pk>[\w-]+)/$', group_detail),
   url(r'^(?P<pk>[\w-]+)/update/$',
       GroupUpdateView.as_view()),
   url(r'^(?P<pk>[\w-]+)/delete/$',
       GroupDeleteView.as_view()),
)
