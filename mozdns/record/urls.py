from django.conf.urls.defaults import url, patterns
from mozdns.record.views import (record_search, record_ajax,
                                 record_search_ajax, record, record_delete)


urlpatterns = patterns(
    '',
    url(r'^record_ajax/$', record_ajax, name='record-ajax'),
    url(r'^search_ajax/$', record_search_ajax,
        name='record-search-ajax'),
    url(r'^search/(?P<record_type>[\w-]+)/$', record_search,
        name='record-search'),
    url(r'^create/(?P<record_type>[\w-]+)/$', record,
        name='record-record'),
    url(r'^update/(?P<record_type>[\w-]+)/(?P<record_pk>\d+)/$',
        record, name='update-record'),
    url(r'^delete/(?P<record_type>[\w-]+)/(?P<record_pk>\d+)/$',
        record_delete, name='delete-record'),
)
