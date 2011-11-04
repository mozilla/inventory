from django.conf.urls.defaults import *
from piston.resource import Resource
from api.handlers import SystemHandler
from api.handlers import NetworkAdapterHandler
from api.handlers import KeyValueHandler
from api.handlers import DHCPHandler

systems_handler = Resource(SystemHandler)
network_adapter_handler = Resource(NetworkAdapterHandler)
keyvalue_handler = Resource(KeyValueHandler)
dhcp_handler = Resource(DHCPHandler)
from django.views.decorators.cache import cache_control
cached_resource = cache_control(public=True, maxage=600, s_maxage=600)

urlpatterns = patterns('',
    url(r'^dhcp/(?P<dhcp_scope>[^/]+)/(?P<dhcp_action>[^/]+)', cached_resource(dhcp_handler)),
    url(r'^dhcp/', cached_resource(dhcp_handler)),
    url(r'^system/(?P<system_id>[^/]+)/', cached_resource(systems_handler)),
    url(r'^systems/', cached_resource(systems_handler)),
    url(r'^keyvalue/(?P<key_value_id>[^/]+)/', cached_resource(keyvalue_handler)),
    url(r'^keyvalue/', cached_resource(keyvalue_handler)),
    url(r'^networkadapter/(?P<network_adapter_id>[^/]+)/', cached_resource(network_adapter_handler)),
    url(r'^networkadapter/', cached_resource(network_adapter_handler)),
      )
