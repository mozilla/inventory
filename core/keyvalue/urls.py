from django.conf.urls.defaults import patterns, url

from django.views.decorators.csrf import csrf_exempt

from core.keyvalue.views import keyvalue, validate_keyvalue_ajax


urlpatterns = patterns('',
    url(r'^(?P<obj_class>[\w-]+)/(?P<obj_pk>\d+)/$', csrf_exempt(keyvalue)),
    url(r'^validate_keyvalue_ajax/$', validate_keyvalue_ajax,
        name='validate-keyvalue-ajax'),)
