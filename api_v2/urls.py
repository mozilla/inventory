from django.conf.urls.defaults import *
from piston.resource import Resource
from api_v2.system_handler import SystemHandler
from api_v2.networkadapter_handler import NetworkAdapterHandler
from api_v2.keyvalue_handler import KeyValueHandler
from api_v2.truth_handler import TruthHandler
from api_v2.dhcp_handler import DHCPHandler
from api_v2.reverse_dns_handler import ReverseDNSHandler
from api_v2.system_rack_handler import SystemRackHandler
from api_v2.system_status_handler import SystemStatusHandler
from django.views.decorators.cache import cache_control
cached_resource = cache_control(public=True, maxage=600, s_maxage=600)

systems_handler = Resource(SystemHandler)
network_adapter_handler = Resource(NetworkAdapterHandler)
keyvalue_handler = Resource(KeyValueHandler)
reverse_dns_handler = Resource(ReverseDNSHandler)
dhcp_handler = Resource(DHCPHandler)
system_rack_handler = Resource(SystemRackHandler)
system_status_handler = Resource(SystemStatusHandler)

urlpatterns = patterns('',
    url(r'^dhcp/(?P<dhcp_scope>[^/]+)/(?P<dhcp_action>[^/]+)', cached_resource(dhcp_handler)),
    url(r'^dhcp/', cached_resource(dhcp_handler)),
    url(r'^reverse_dns/(?P<reverse_dns_zone>[^/]+)/(?P<reverse_dns_action>[^/]+)', cached_resource(reverse_dns_handler)),
    url(r'^reverse_dns/', cached_resource(reverse_dns_handler)),
    url(r'^system/(?P<system_id>[^/]+)/', cached_resource(systems_handler)),
    url(r'^systems/', cached_resource(systems_handler)),
    url(r'^systemrack/(?P<system_rack_id>[^/]+)/', cached_resource(system_rack_handler)),
    url(r'^systemrack/', cached_resource(system_rack_handler)),
    url(r'^systemstatus/(?P<system_status_id>[^/]+)/', cached_resource(system_status_handler)),
    url(r'^systemstatus/', cached_resource(system_status_handler)),
    url(r'^keyvalue/(?P<key_value_id>[^/]+)/', cached_resource(keyvalue_handler)),
    url(r'^keyvalue/', cached_resource(keyvalue_handler)),
    url(r'^networkadapter/(?P<network_adapter_id>[^/]+)/', cached_resource(network_adapter_handler)),
    url(r'^networkadapter/', cached_resource(network_adapter_handler)),
      )
