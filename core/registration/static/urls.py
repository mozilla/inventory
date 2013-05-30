from django.conf.urls.defaults import patterns, url
from core.registration.static.views import ajax_create_sreg

urlpatterns = patterns('',
   url(r'^create[/]$', ajax_create_sreg),
)
