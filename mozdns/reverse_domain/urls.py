from django.conf.urls.defaults import *
from django.views.decorators.csrf import csrf_exempt

from mozdns.reverse_domain.views import *

urlpatterns = patterns('mozdns.reverse_domain.views',
    url(r'^$', ReverseDomainListView.as_view()),
    url(r'bootstrap_ipv6/$', csrf_exempt('bootstrap_ipv6')),
    url(r'create/$', csrf_exempt(ReverseDomainCreateView.as_view())),
    url(r'(?P<pk>[\w-]+)/update/$',
        csrf_exempt(ReverseDomainUpdateView.as_view())),
    url(r'(?P<pk>[\w-]+)/delete/$',
        csrf_exempt(ReverseDomainDeleteView.as_view())),
    url(r'(?P<pk>[\w-]+)/inheirit_soa/$', csrf_exempt('inheirit_soa')),
    url(r'(?P<pk>[\w-]+)/$', csrf_exempt(ReverseDomainDetailView.as_view())),
)
