from django.conf.urls.defaults import *
from django.views.decorators.csrf import csrf_exempt

from mozdns.view.views import *

urlpatterns = patterns('',
    url(r'^$', ViewListView.as_view()),
    url(r'(?P<domain>[\w-]+)/create/$', csrf_exempt(ViewCreateView.as_view())),
    url(r'create/$', csrf_exempt(ViewCreateView.as_view())),
    url(r'(?P<pk>[\w-]+)/update/$', csrf_exempt(ViewUpdateView.as_view())),
    url(r'(?P<pk>[\w-]+)/delete/$', csrf_exempt(ViewDeleteView.as_view())),
    url(r'(?P<pk>[\w-]+)/$', csrf_exempt(ViewDetailView.as_view())),
)
