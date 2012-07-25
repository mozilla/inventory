from tastypie import fields
from tastypie.authorization import DjangoAuthorization
from django.core.exceptions import ValidationError
from tastypie.authentication import Authentication
#from tastytools.resources import ModelResource
from tastypie.resources import ModelResource
from tastypie.resources import ALL, ALL_WITH_RELATIONS
import systems.models as system_model
from django.conf.urls.defaults import url
from tastypie.serializers import Serializer
from django.core.serializers import json as djson
from tastytools.test.resources import ResourceTestData
from tastypie.authorization import Authorization
from core.interface.static_intr.models import StaticInterface
from core.interface.static_intr.models import StaticIntrKeyValue
from mozdns.domain.models import Domain
import json
class PrettyJSONSerializer(Serializer):
    json_indent = 2

    def to_json(self, data, options=None):
        options = options or {}
        data = self.to_simple(data, options)
        return json.dumps(data, cls=djson.DjangoJSONEncoder,
                sort_keys=True, ensure_ascii=False, indent=self.json_indent)

class CustomAPIResource(ModelResource):
    def __init__(self, *args, **kwargs):
        super(CustomAPIResource, self).__init__(*args, **kwargs)

    def determine_format(self, request):
        format = request.GET.get('format')
        if format:
            return super(CustomAPIResource, self).determine_format(request)
        else: 
            return "application/json"

    class Meta:
        serializer = PrettyJSONSerializer()
        authorization= Authorization()
        authentication = Authentication()
        allowed_methods = ['get', 'post', 'put', 'delete', 'patch', 'PATCH']

class SystemResource(CustomAPIResource):

    key_value = fields.ToManyField('api_v3.system_api.KeyValueResource', 'keyvalue_set', full=True, null=True)
    server_model = fields.ForeignKey('api_v3.system_api.ServerModelResource', 'server_model', null=True, full=True)
    operating_system = fields.ForeignKey('api_v3.system_api.OperatingSystemResource', 'operating_system', null=True, full=True)
    system_rack = fields.ForeignKey('api_v3.system_api.SystemRackResource', 'system_rack', null=True, full=True)

    def process_extra(self, bundle, request, **kwargs):
        patch_dict = json.loads(request.POST.items()[0][0])

        ## Entry point for adding a new adapter by mac address via the rest API
        if patch_dict.has_key('mac_address') and patch_dict.has_key('auto_create_interface') and patch_dict['auto_create_interface'].upper() == 'TRUE':
            mac_addr = patch_dict.pop('mac_address')
            patch_dict.pop('auto_create_interface')
            ip_str = patch_dict.pop('ip_address', None)
            sys = bundle.obj
            label = sys.hostname.split('.')[0]
            domain_parsed = ".".join(sys.hostname.split('.')[1:]) + '.mozilla.com'
            domain = Domain.objects.filter(name=domain_parsed)[0]
            # ip_str will get auto generated eventually
            if not ip_str:
                ip_str = '10.99.99.97'
            try:
                s = StaticInterface(label=label, mac=mac_addr, domain=domain, ip_str=ip_str, ip_type='4', system=sys)
                s.clean()
                s.save()
                s.update_attrs()
                s.attrs.primary = '4'
                s.attrs.interface_type = 'eth'
                s.attrs.alias = '0'
            except ValidationError, e:
                bundle.errors['error_message'] = " ".join(e.messages)
            except Exception, e:
                print e

    def obj_create(self, bundle, request, **kwargs):
        ret_bundle = super(SystemResource, self).obj_create(bundle, request, **kwargs)
        self.process_extra(ret_bundle, request, **kwargs)

    def obj_update(self, bundle, request, **kwargs):
        ret_bundle = super(SystemResource, self).obj_update(bundle, request, **kwargs)
        self.process_extra(ret_bundle, request, **kwargs)


    def prepend_urls(self):
            return [
                url(r"^(?P<resource_name>%s)/(?P<id>[\d]+)/$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_system_dispatch_by_id_detail"),
                url(r"^(?P<resource_name>%s)/(?P<hostname>[^schema].*)/$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_system_dispatch_by_hostname_detail"),
            ]
    class Meta(CustomAPIResource.Meta):
        filtering = {
                'hostname': ALL_WITH_RELATIONS,
                'system_rack': ALL_WITH_RELATIONS,
                'notes': ALL,
                'asset_tag': ALL,
                'key_value': ALL_WITH_RELATIONS,
                'key_value__key': ALL_WITH_RELATIONS,
                }
        fields = [
                    
                ]
        exclude = [
                'key_value__system',

                ]
        resource_name = 'system'
        queryset = system_model.System.objects.all()

class ServerModelResource(CustomAPIResource):
    class Meta(CustomAPIResource.Meta):
        filtering = {
            'name': ALL,
            'vendor': ALL,
            'model': ALL


        }
        serializer = PrettyJSONSerializer()
        resource_name = 'server_model'
        queryset = system_model.ServerModel.objects.all()

class AllocationResource(CustomAPIResource):
    class Meta(CustomAPIResource.Meta):
        resource_name = 'allocation'
        queryset = system_model.Allocation.objects.all()

class LocationResource(CustomAPIResource):
    class Meta(CustomAPIResource.Meta):
        resource_name = 'location'
        queryset = system_model.Location.objects.all()

class SystemRackResource(CustomAPIResource):
    class Meta(CustomAPIResource.Meta):
        resource_name = 'system_rack'
        queryset = system_model.SystemRack.objects.all()

        filtering = {
                'name': ALL_WITH_RELATIONS,
                'id': ALL_WITH_RELATIONS,
                }
class SystemStatusResource(CustomAPIResource):
    class Meta(CustomAPIResource.Meta):
        resource_name = 'system_status'
        queryset = system_model.SystemStatus.objects.all()



class OperatingSystemResource(CustomAPIResource):
        
    class Meta(CustomAPIResource.Meta):
        def __init__(self, *args, **kwargs):
            import pdb; pdb.set_trace()
            super(Meta, self).__init(*args, **kwargs)
        resource_name = 'operating_system'
        queryset = system_model.OperatingSystem.objects.all()

class OperatingSystemData(CustomAPIResource):
    resource = "operating_system"

    def get_data(self, data):
        data.set('id', '8')
        data.set('name', 'RHEL')
        data.set('resource_uri', '/tasty/v3/operating_system/8/')
        data.set('version', '6.2')
        return data
class KeyValueResource(CustomAPIResource):
    #system = fields.ToOneField(SystemResource, 'system', full=True)

    class Meta(CustomAPIResource.Meta):
        filtering = {
                'system': ALL_WITH_RELATIONS,
                'key': ALL_WITH_RELATIONS,
                'value': ALL_WITH_RELATIONS,
                }
        resource_name = 'key_value'
        queryset = system_model.KeyValue.objects.all()
