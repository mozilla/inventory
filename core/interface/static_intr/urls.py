from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^$', AddressRecordListView.as_view()),
    url(r'(?P<domain>[\w-]+)/create/$', AddressRecordCreateView.as_view()),
    url(r'create/$', AddressRecordCreateView.as_view()),
    url(r'(?P<pk>[\w-]+)/update/$', AddressRecordUpdateView.as_view()),
    url(r'(?P<pk>[\w-]+)/delete/$', AddressRecordDeleteView.as_view()),
    url(r'(?P<pk>[\w-]+)/$', AddressRecordDetailView.as_view()),
)   
