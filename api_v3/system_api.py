from tastypie import fields
from tastypie.authorization import DjangoAuthorization
from tastypie.resources import ModelResource, ALL, ALL_WITH_RELATIONS
import systems.models as system_model
from django.conf.urls.defaults import url
from tastypie.serializers import Serializer
from django.core.serializers import json as djson
import json
class PrettyJSONSerializer(Serializer):
    json_indent = 2

    def to_json(self, data, options=None):
        options = options or {}
        data = self.to_simple(data, options)
        return json.dumps(data, cls=djson.DjangoJSONEncoder,
                sort_keys=True, ensure_ascii=False, indent=self.json_indent)

class SystemResource(ModelResource):
    key_value = fields.ToManyField('api_v3.system_api.KeyValueResource', 'key_values', full=True, null=True)
    server_model = fields.ForeignKey('api_v3.system_api.ServerModelResource', 'server_model', null=True, full=True)
    operating_system = fields.ForeignKey('api_v3.system_api.OperatingSystemResource', 'operating_system', null=True, full=True)
    system_rack = fields.ForeignKey('api_v3.system_api.SystemRackResource', 'system_rack', null=True, full=True)
    
    def prepend_urls(self):
            return [
                url(r"^(?P<resource_name>%s)/(?P<id>[\d]+)/$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_system_dispatch_by_id_detail"),
                url(r"^(?P<resource_name>%s)/(?P<hostname>.*)/$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_system_dispatch_by_hostname_detail"),
            ]
    class Meta:
        serializer = PrettyJSONSerializer()
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

class ServerModelResource(ModelResource):
    class Meta:
        serializer = PrettyJSONSerializer()
        resource_name = 'server_model'
        queryset = system_model.ServerModel.objects.all()

class AllocationResource(ModelResource):
    class Meta:
        resource_name = 'allocation'
        queryset = system_model.Allocation.objects.all()

class LocationResource(ModelResource):
    class Meta:
        resource_name = 'location'
        queryset = system_model.Location.objects.all()

class SystemRackResource(ModelResource):
    class Meta:
        resource_name = 'system_rack'
        queryset = system_model.SystemRack.objects.all()

        filtering = {
                'name': ALL_WITH_RELATIONS,
                'id': ALL_WITH_RELATIONS,
                }
class SystemStatusResource(ModelResource):
    class Meta:
        resource_name = 'system_status'
        queryset = system_model.SystemStatus.objects.all()

class OperatingSystemResource(ModelResource):
    class Meta:
        resource_name = 'operating_system'
        queryset = system_model.OperatingSystem.objects.all()

class KeyValueResource(ModelResource):
    system = fields.ToOneField(SystemResource, 'system', full=False)

    class Meta:
        filtering = {
                'system': ALL_WITH_RELATIONS,
                'key': ALL_WITH_RELATIONS,
                'value': ALL_WITH_RELATIONS,
                }
        resource_name = 'key_value'
        queryset = system_model.KeyValue.objects.all()
