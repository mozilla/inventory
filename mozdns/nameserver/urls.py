from django.conf.urls.defaults import *
from django.views.decorators.csrf import csrf_exempt

from mozdns.nameserver.views import *

urlpatterns = patterns('',
    url(r'^$', NSListView.as_view()),
    url(r'(?P<domain>[\w-]+)/create_delegated/$',
        csrf_exempt(create_ns_delegated)),
    url(r'(?P<domain>[\w-]+)/create/$', csrf_exempt(NSCreateView.as_view())),
    url(r'create/$', csrf_exempt(NSCreateView.as_view())),
    url(r'(?P<nameserver_pk>[\w-]+)/update/$', csrf_exempt(update_ns)),
    url(r'(?P<pk>[\w-]+)/delete/$', csrf_exempt(NSDeleteView.as_view())),
    url(r'(?P<pk>[\w-]+)/$', csrf_exempt(NSDetailView.as_view())),
)
