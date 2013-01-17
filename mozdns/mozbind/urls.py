from django.conf.urls.defaults import patterns, url
from django.views.decorators.csrf import csrf_exempt

from mozdns.mozbind.views import build_debug_soa

urlpatterns = patterns('',
                       url(r'^build_debug/(?P<soa_pk>[\w-]+)/$',
                           csrf_exempt(build_debug_soa)),
                       )
