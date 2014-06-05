from django.conf.urls.defaults import patterns, url, include

from django.views.decorators.csrf import csrf_exempt

from core.api.v1.api import v1_core_api
from core.views import core_index


urlpatterns = patterns(
    '',
    url(r'^$', csrf_exempt(core_index), name='core-index'),
    url(r'^api/', include(v1_core_api.urls)),
    url(r'^dhcp/', include('core.dhcp.urls')),
    url(r'^group/', include('core.group.urls')),
    url(r'^hwadapter/', include('core.hwadapter.urls')),
    url(r'^keyvalue/', include('core.keyvalue.urls')),
    url(r'^network/', include('core.network.urls')),
    url(r'^range/', include('core.range.urls')),
    url(r'^registration/', include('core.registration.urls')),
    url(r'^site/', include('core.site.urls')),
    url(r'^search/', include('core.search.urls')),
    url(r'^service/', include('core.service.urls')),
    url(r'^vlan/', include('core.vlan.urls')),
)
