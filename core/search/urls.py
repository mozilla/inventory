from django.conf.urls.defaults import *
from django.views.decorators.csrf import csrf_exempt

from core.search.views import *

urlpatterns = patterns('',
    url(r'^search_ajax', csrf_exempt(search_ajax)),
    url(r'^search_json', csrf_exempt(search_json)),
    url(r'^get_zones_json', csrf_exempt(get_zones_json)),
    url(r'^$', csrf_exempt(search)),
)
