from django.conf.urls.defaults import *
from django.views.decorators.csrf import csrf_exempt

from mozdns.mozbind.views import *

urlpatterns = patterns('',
    url(r'^(?P<soa_pk>[\w-]+)/build/$',
        csrf_exempt(build_forward_soa)),
)
