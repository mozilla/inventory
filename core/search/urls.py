from django.conf.urls.defaults import patterns, url
from django.views.decorators.csrf import csrf_exempt

from core.search.views import (
    search_ajax, search_dns_text, get_zones_json, search, ajax_type_search,
    search_schema_ajax
)

urlpatterns = patterns(
    '',
    url(r'^search_schema', search_schema_ajax),
    url(r'^search_ajax', csrf_exempt(search_ajax)),
    url(r'^search_dns_text', csrf_exempt(search_dns_text)),
    url(r'^get_zones_json', csrf_exempt(get_zones_json)),
    url(r'^ajax_type_search', csrf_exempt(ajax_type_search)),
    url(r'^$', csrf_exempt(search), name='core-search'),
)
