from django.conf.urls.defaults import *
from system_api import SystemResource, ServerModelResource, OperatingSystemResource, KeyValueResource, AllocationResource, LocationResource, SystemRackResource, SystemStatusResource
from system_api import PortDataResource, AdvisoryDataResource
from system_api import OperatingSystemData
#from tastypie.api import Api
from tastytools.api import Api

v3_api = Api(api_name='v3')
v3_api.register(SystemResource())
v3_api.register(ServerModelResource())
v3_api.register(OperatingSystemResource())
v3_api.register(KeyValueResource())
v3_api.register(AllocationResource())
v3_api.register(LocationResource())
v3_api.register(SystemRackResource())
v3_api.register(SystemStatusResource())
v3_api.register(AdvisoryDataResource())
v3_api.register(PortDataResource())
v3_api.register_testdata(OperatingSystemData)
urlpatterns = patterns('',
    (r'', include(v3_api.urls)),
    (r'^tastytools/', include('tastytools.urls'), {'api_name': v3_api.api_name}),
)
