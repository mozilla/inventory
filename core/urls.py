from django.conf.urls.defaults import *

from core.interface.static_intr.views import create_static_interface
from core.interface.static_intr.views import edit_static_interface
from core.interface.static_intr.views import find_available_ip_from_network

from django.views.decorators.csrf import csrf_exempt

from core.views import search_ip

urlpatterns = patterns('',

    url(r'^$', csrf_exempt(search_ip)),
    url(r'^interface/',include('core.interface.urls')),
    url(r'^find_available_ip_from_network/$',
        csrf_exempt(find_available_ip_from_network)),


    url(r'^vlan/',include('core.vlan.urls')),
    url(r'^network/',include('core.network.urls')),
    url(r'^site/',include('core.site.urls')),
)
