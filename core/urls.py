from django.conf.urls.defaults import *

from core.interface.static_intr.views import create_static_interface
from core.interface.static_intr.views import edit_static_interface
from core.interface.static_intr.views import find_available_ip_from_network

from django.views.decorators.csrf import csrf_exempt

urlpatterns = patterns('',
    #url(r'^$', direct_to_template, {'template': 'mozdns.html'}),

    url(r'^interface/(?P<system_pk>[\w-]+)/create/$',
        csrf_exempt(create_static_interface)),
    url(r'^interface/(?P<system_pk>[\w-]+)/(?P<intr_pk>[\w-]+)/update/$',
        csrf_exempt(edit_static_interface)),
    url(r'^find_available_ip_from_network/$',
        csrf_exempt(find_available_ip_from_network)),

)
