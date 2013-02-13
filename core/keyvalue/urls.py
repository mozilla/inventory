from django.conf.urls.defaults import patterns, url

from django.views.decorators.csrf import csrf_exempt

from core.keyvalue.views import keyvalue, validate_keyvalue_ajax


urlpatterns = patterns('',
    url(r'^$', csrf_exempt(keyvalue), name='keyvalue'),
    url(r'^validate_keyvalue_ajax/$', validate_keyvalue_ajax,
        name='validate-keyvalue-ajax'),)
