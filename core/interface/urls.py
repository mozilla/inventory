from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template

from core.interface.static_intr.views import *
from django.views.decorators.csrf import csrf_exempt

urlpatterns = patterns('',
    url(r'^create/$',
        csrf_exempt(create_no_system_static_interface)),
    url(r'^(?P<system_pk>[\w-]+)/create/$',
        csrf_exempt(create_static_interface)),
    url(r'^(?P<system_pk>[\w-]+)/quick_create/$',
        csrf_exempt(quick_create)),
    url(r'^(?P<intr_pk>[\w-]+)/$',
        csrf_exempt(detail_static_interface)),
    url(r'^(?P<intr_pk>[\w-]+)/update/$',
        csrf_exempt(edit_static_interface)),
    url(r'^(?P<intr_pk>[\w-]+)/delete/$',
        csrf_exempt(delete_static_interface)),
    url(r'^(?P<system_pk>[\w-]+)/(?P<intr_pk>[\w-]+)/remove_attr/(?P<attr_pk>[\w-]+)/$',
        csrf_exempt(delete_attr)),
)

