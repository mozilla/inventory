from django.conf.urls.defaults import *
from django.views.decorators.csrf import csrf_exempt

from core.search.views import *

urlpatterns = patterns('',
    url(r'^search_ajax', csrf_exempt(search_ajax)),
    url(r'^$', csrf_exempt(search)),
)
