from django.conf.urls.defaults import patterns, url

from core.service.views import *  # noqa


urlpatterns = patterns(
    '',
    url(r'^$', ServiceListView.as_view(), name='service'),
    url(r'^create/$', ServiceCreateView.as_view()),
    url(r'^(?P<pk>[\w-]+)/$', service_detail),
    url(r'^(?P<pk>[\w-]+)/update/$', ServiceUpdateView.as_view()),
    url(r'^(?P<pk>[\w-]+)/delete/$', ServiceDeleteView.as_view()),
)
