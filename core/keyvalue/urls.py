from django.conf.urls.defaults import patterns, url

from django.views.decorators.csrf import csrf_exempt

from core.keyvalue.views import keyvalue


urlpatterns = patterns('',
                       url(r'^$', csrf_exempt(keyvalue), name='keyvalue'),
                       )
