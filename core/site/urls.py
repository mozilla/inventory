from django.conf.urls.defaults import patterns, url

from core.site.views import *

urlpatterns = patterns('',
   url(r'^$', SiteListView.as_view()),
   url(r'^create/$', SiteCreateView.as_view()),
   url(r'^(?P<site_pk>[\w-]+)/$', site_detail),
   url(r'^(?P<pk>[\w-]+)/update/$', SiteUpdateView.as_view()),
   url(r'^(?P<pk>[\w-]+)/delete/$', SiteDeleteView.as_view()),
)
