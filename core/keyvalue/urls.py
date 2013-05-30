from django.conf.urls.defaults import patterns, url

from django.views.decorators.csrf import csrf_exempt

from core.keyvalue.views import keyvalue, validate_keyvalue_ajax
from core.keyvalue.api import *


urlpatterns = patterns('',
    url(r'^(?P<obj_class>[\w-]+)/(?P<obj_pk>\d+)/$', csrf_exempt(keyvalue)),
    url(r'^validate_keyvalue_ajax/$', validate_keyvalue_ajax,
        name='validate-keyvalue-ajax'),

    url(r'api/(?P<kv_class>[\w-]+)/(?P<obj_pk>\d+)/create/', kv_create),
    url(r'api/(?P<kv_class>[\w-]+)/(?P<obj_pk>\d+)/list/', kv_list),
    url(r'api/(?P<kv_class>[\w-]+)/(?P<kv_pk>\d+)/update/', kv_update),
    url(r'api/(?P<kv_class>[\w-]+)/(?P<kv_pk>\d+)/delete/', kv_delete),
    url(r'api/(?P<kv_class>[\w-]+)/(?P<kv_pk>\d+)/detail/', kv_detail),
)
