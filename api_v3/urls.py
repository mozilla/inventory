from django.conf.urls.defaults import *
from system_api import SystemResource, ServerModelResource, OperatingSystemResource, KeyValueResource
from tastypie.api import Api

v3_api = Api(api_name='v3')
v3_api.register(SystemResource())
v3_api.register(ServerModelResource())
v3_api.register(OperatingSystemResource())
v3_api.register(KeyValueResource())
urlpatterns = patterns('',
    (r'', include(v3_api.urls)),
)
