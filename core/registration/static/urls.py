from django.conf.urls.defaults import patterns, url
from core.registration.static.views import (
    ajax_create_sreg, combine_status_list, ajax_combine_sreg
)

urlpatterns = patterns(
    '',
    url(r'^create[/]$', ajax_create_sreg),
    url(r'^combine[/]$', ajax_combine_sreg),
    url(r'^debug_combine_status_list[/]$', combine_status_list),
)
