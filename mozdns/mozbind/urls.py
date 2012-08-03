from django.conf.urls.defaults import *
from django.views.decorators.csrf import csrf_exempt

from mozdns.mozbind.views import *

urlpatterns = patterns('',
    url(r'^forward/(?P<soa_pk>[\w-]+)/build_debug/$',
        csrf_exempt(build_forward_soa)),
    url(r'^reverse/(?P<soa_pk>[\w-]+)/build_debug/$',
        csrf_exempt(build_reverse_soa)),
    url(r'^build/(?P<soa_pk>[\w-]+)/$',
        csrf_exempt(build_soa)),
)
