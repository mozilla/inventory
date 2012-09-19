from django.conf.urls.defaults import *

from mozdns.domain.views import *
from django.views.decorators.csrf import csrf_exempt

urlpatterns = patterns('',
    url(r'^$', DomainListView.as_view()),
    url(r'^reverse_domains/$', ReverseDomainListView.as_view()),
    url(r'^get_all_domains/$', get_all_domains),
    url(r'create/$', csrf_exempt(DomainCreateView.as_view())),
    url(r'(?P<pk>[\w-]+)/update/$', csrf_exempt(DomainUpdateView.as_view())),
    url(r'(?P<pk>[\w-]+)/delete/$', csrf_exempt(DomainDeleteView.as_view())),
    url(r'(?P<pk>[\w-]+)/$', csrf_exempt(DomainDetailView.as_view())),
)
