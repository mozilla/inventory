from django.conf.urls.defaults import *
from django.views.decorators.csrf import csrf_exempt

from core.range.views import *

urlpatterns = patterns('',
    url(r'^$', csrf_exempt(RangeListView.as_view())),
    url(r'create/$', csrf_exempt(RangeCreateView.as_view())),
    url(r'(?P<range_pk>[\w-]+)/update/$', csrf_exempt(update_range)),
    url(r'attr/(?P<attr_pk>[\w-]+)/delete/$', csrf_exempt(delete_range_attr)),
    url(r'(?P<pk>[\w-]+)/delete/$',
        csrf_exempt(RangeDeleteView.as_view())),
    url(r'(?P<range_pk>[\w-]+)/$', csrf_exempt(range_detail)),
)
