from django.conf.urls.defaults import *
from django.views.decorators.csrf import csrf_exempt

from mozdns.cname.views import *

urlpatterns = patterns('',
    url(r'^$', CNAMEListView.as_view()),
    url(r'(?P<domain>[\w-]+)/create/$',
        csrf_exempt(CNAMECreateView.as_view())),
    url(r'create/$', csrf_exempt(CNAMECreateView.as_view())),
    url(r'(?P<pk>[\w-]+)/update/$', csrf_exempt(CNAMEUpdateView.as_view())),
    url(r'(?P<pk>[\w-]+)/delete/$', csrf_exempt(CNAMEDeleteView.as_view())),
    url(r'(?P<pk>[\w-]+)/$', csrf_exempt(CNAMEDetailView.as_view())),
)
