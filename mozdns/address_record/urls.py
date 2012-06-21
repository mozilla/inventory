from django.conf.urls.defaults import *
from django.views.decorators.csrf import csrf_exempt

from mozdns.address_record.views import *

urlpatterns = patterns('',
    url(r'^$', csrf_exempt(AddressRecordListView.as_view())),
    url(r'(?P<domain>[\w-]+)/create/$',
        csrf_exempt(AddressRecordCreateView.as_view())),
    url(r'create/$', csrf_exempt(AddressRecordCreateView.as_view())),
    url(r'(?P<pk>[\w-]+)/update/$',
        csrf_exempt(AddressRecordUpdateView.as_view())),
    url(r'(?P<pk>[\w-]+)/delete/$',
        csrf_exempt(AddressRecordDeleteView.as_view())),
    url(r'(?P<pk>[\w-]+)/$', csrf_exempt(AddressRecordDetailView.as_view())),
)
