from django.conf.urls.defaults import *
from django.views.decorators.csrf import csrf_exempt

from core.build.views import *

urlpatterns = patterns('',
    url(r'(?P<network_pk>[\w-]+)/$',
        csrf_exempt(build_network)),
)
