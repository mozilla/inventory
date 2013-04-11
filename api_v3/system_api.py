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
from core.range.models import Range
from mozdns.view.models import View
from mozdns.domain.models import Domain
from core.lib.utils import create_ipv4_intr_from_domain
import json
import re
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
    system_status = fields.ForeignKey('api_v3.system_api.SystemStatusResource', 'system_status', null=True, full=True)
    operating_system = fields.ForeignKey('api_v3.system_api.OperatingSystemResource', 'operating_system', null=True, full=True)
    system_rack = fields.ForeignKey('api_v3.system_api.SystemRackResource', 'system_rack', null=True, full=True)
    allocation = fields.ForeignKey('api_v3.system_api.AllocationResource', 'allocation', null=True, full=True)
    """
        Do not enable the following. It will fail due to the m2m validation routine written by uberj.
        Instead I'm overriding full_dehydrate to get the attributes that we want
        interface = fields.ToManyField('api_v3.system_api.StaticInterfaceResource', 'staticinterface_set', null=True, full=True)
    """

    def __init__(self, *args, **kwargs):
        super(SystemResource, self).__init__(*args, **kwargs)


    def get_schema(self, request, **kwargs):
        ret = super(SystemResource, self).get_schema(request, **kwargs)
        retjson = json.loads(ret.content)
        retjson['fields']['auto_create_interface'] = {
                'nullable': True,
                'default': False,
                'type': 'boolean',
                'unique': False,
                'help_text': 'auto_create_interface="True"',
                'example': 'auto_create_interface="True"',
                }
        retjson['fields']['delete_interface'] = {
                'nullable': True,
                'default': False,
                'type': 'boolean',
                'unique': False,
                'help_text': 'Set this to delete an interfacedelete_interface="True"',
                'example': 'delete_interface="True"',
                }
        retjson['fields']['update_interface'] = {
                'nullable': True,
                'default': False,
                'type': 'boolean',
                'unique': False,
                'help_text': 'Set this to update an interface update_interface="True"',
                'example': 'update_interface="True"',
                }
        retjson['fields']['ip_address'] = {
                'nullable': True,
                'default': False,
                'type': 'string',
                'unique': False,
                'help_text': 'ip_address="10.0.0.1"',
                'example': 'ip_address="10.0.0.1"',
                }
        retjson['fields']['mac_address'] = {
                'nullable': True,
                'default': False,
                'type': 'string',
                'unique': False,
                'help_text': 'mac_address="00:00:00:00:00:00"',
                'example': 'mac_address="00:00:00:00:00:00"',
                }
        retjson['fields']['interface'] = {
                'nullable': True,
                'default': False,
                'type': 'string',
                'unique': False,
                'help_text': 'interface="eth0.0"',
                'example': 'interface="eth0.0"',
                }
        ret.content = json.dumps(retjson)
        return ret


    @staticmethod
    def extract_nic_attrs(nic_name):
        nic_type, primary, alias = "eth", 0, 0
        m = re.search("(eth|mgmt)(\d+)\.(\d+)", nic_name)
        if m:
            nic_type = m.group(1) if m.group(1) else "eth"
            primary = m.group(2) if m.group(2) else "0"
            nic_alias = m.group(3) if m.group(3) else "0"
            return nic_type, primary, nic_alias
        else:
            raise ValidationError("Invalid format for adapter name. ex: eth0.0")

    def process_extra(self, bundle, request, **kwargs):
        patch_dict = json.loads(request.POST.items()[0][0])

        if patch_dict.has_key('delete_interface') and patch_dict.has_key('interface'):
            patch_dict.pop('delete_interface')
            sys = bundle.obj
            interface = patch_dict.pop('interface', None)
            if sys and interface:
                sys.delete_adapter(interface)

        if patch_dict.has_key('update_interface') and patch_dict.has_key('interface'):
            patch_dict.pop('update_interface')
            sys = bundle.obj
            if 'interface' in patch_dict:
                sys.update_adapter(**patch_dict)

        ## Entry point for adding a new adapter by mac address via the rest API
        if patch_dict.has_key('mac'):

            enable_dns = True
            enable_private = True
            enable_public = False
            sys = bundle.obj
            range = patch_dict.pop('range', None)
            fqdn = patch_dict.pop('fqdn', None)
            ip_str = patch_dict.pop('ip_address', None)
            interface = patch_dict.pop('interface', None)
            domain = patch_dict.pop('domain', 'mozilla.com')
            from core.lib.utils import create_ipv4_intr_from_range
            mac = patch_dict['mac']
            if interface:
                interface_type, primary, alias = SystemResource.extract_nic_attrs(interface)
            else:
                interface_type, primary, alias = sys.get_next_adapter()

            if not fqdn:
                domain_parsed = ".".join(sys.hostname.split('.')[1:]) + '.' + domain
                domain_name = domain_parsed.lower()
                label = sys.hostname.split('.')[0]
            else:
                domain_parsed = ".".join(fqdn.split('.')[1:])
                domain_name = domain_parsed.lower()
                label = fqdn.split('.')[0]


            if range:
                range_start_str = range.split(',')[0]
                range_end_str = range.split(',')[1]
                s, errors = create_ipv4_intr_from_range(label, domain_name, sys, mac, range_start_str, range_end_str)
            if ip_str:
                domain = Domain.objects.filter(name=domain_parsed)[0]
                s = StaticInterface(label=label, mac=mac, domain=domain, ip_str=ip_str, ip_type='4', system=sys)
            try:
                if s:
                    s.save()
                    s.update_attrs()
                    if enable_dns and enable_public:
                        private = View.objects.get(name='private')
                        s.views.add(private)
                        s.save()

                    elif enable_dns and enable_private and not enable_public:
                        private = View.objects.get(name='private')
                        s.views.add(private)
                        s.save()

                    if interface:
                        interface_type, primary, alias = SystemResource.extract_nic_attrs(interface)
                    else:
                        interface_type, primary, alias = sys.get_next_adapter()

                    s.attrs.primary = primary
                    s.attrs.interface_type = interface_type
                    s.attrs.alias = alias
                else:
                    print 'We failed'
                    bundle.errors['error_message'] = "Unable to create adapter for unknown reason"
                    raise ValidationError(join(e.messages))
            except ValidationError, e:
                bundle.errors['error_message'] = " ".join(e.messages)
                raise ValidationError(join(e.messages))
            except Exception, e:
                print e


    def obj_create(self, bundle, request, **kwargs):
        ret_bundle = super(SystemResource, self).obj_create(bundle, request, **kwargs)
        self.process_extra(ret_bundle, request, **kwargs)

    def obj_update(self, bundle, request, **kwargs):
        for intr in bundle.obj.staticinterface_set.all():
            intr.update_attrs()
        ret_bundle = super(SystemResource, self).obj_update(bundle, request, **kwargs)
        ret_bundle = self.process_extra(ret_bundle, request, **kwargs)
        return ret_bundle

    def full_dehydrate(self, bundle):
        """
            Overrideing full dehydrate here. We want to display the iinterface
            attributes, but fails due to m2m validation.
        """
        super(SystemResource, self).full_dehydrate(bundle)
        for intr in bundle.obj.staticinterface_set.all():
            intr.update_attrs()
            if hasattr(intr, 'attrs'):
                if hasattr(intr.attrs, 'primary'):
                    bundle.data['interface:%s%s.%s:ip_address' % (intr.attrs.interface_type, intr.attrs.primary, intr.attrs.alias)] = intr.ip_str
                    bundle.data['interface:%s%s.%s:fqdn' % (intr.attrs.interface_type, intr.attrs.primary, intr.attrs.alias)] = intr.fqdn
                    bundle.data['interface:%s%s.%s:mac_address' % (intr.attrs.interface_type, intr.attrs.primary, intr.attrs.alias)] = intr.mac
                    bundle.data['interface:%s%s.%s:dns_enabled' % (intr.attrs.interface_type, intr.attrs.primary, intr.attrs.alias)] = intr.dns_enabled
                    bundle.data['interface:%s%s.%s:dhcp_enabled' % (intr.attrs.interface_type, intr.attrs.primary, intr.attrs.alias)] = intr.dhcp_enabled
                    bundle.data['interface:%s%s.%s:label' % (intr.attrs.interface_type, intr.attrs.primary, intr.attrs.alias)] = intr.label
        #bundle.data['interface'] = "%s%s.%s" %\
        #(bundle.obj.attrs.interface_type,
        #    bundle.obj.attrs.primary, bundle.obj.attrs.alias)
        #del bundle.data['ip_lower']
        #del bundle.data['ip_upper']
        #del bundle.data['resource_uri']
        return bundle


    def prepend_urls(self):
            return [
                url(r"^(?P<resource_name>%s)/(?P<id>[\d]+)/$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_system_dispatch_by_id_detail"),
                url(r"^(?P<resource_name>%s)/(?P<hostname>[^schema].*)/$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_system_dispatch_by_hostname_detail"),
            ]
    class Meta(CustomAPIResource.Meta):
        filtering = {
                'hostname': ALL_WITH_RELATIONS,
                'system_rack': ALL_WITH_RELATIONS,
                'system_status': ALL_WITH_RELATIONS,
                'notes': ALL,
                'asset_tag': ALL,
                'key_value': ALL_WITH_RELATIONS,
                'allocation': ALL_WITH_RELATIONS,
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
        filtering = {
            'name': ALL,
        }
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

class AdvisoryDataResource(CustomAPIResource):
    class Meta(CustomAPIResource.Meta):
        resource_name = 'advisory_data'
        queryset = system_model.AdvisoryData.objects.all()
        filtering = {
                'ip_address': ALL_WITH_RELATIONS,
                'title': ALL_WITH_RELATIONS,
                'severity': ALL_WITH_RELATIONS,
                'references': ALL_WITH_RELATIONS,
                'advisory': ALL_WITH_RELATIONS,
                }

class PortDataResource(CustomAPIResource):
    class Meta(CustomAPIResource.Meta):
        resource_name = 'port_data'
        queryset = system_model.PortData.objects.all()
        filtering = {
                'ip_address': ALL_WITH_RELATIONS,
                'state': ALL_WITH_RELATIONS,
                'service': ALL_WITH_RELATIONS,
                'port': ALL_WITH_RELATIONS,
                }

class SystemStatusResource(CustomAPIResource):
    class Meta(CustomAPIResource.Meta):
        resource_name = 'system_status'
        queryset = system_model.SystemStatus.objects.all()
        filtering = {
                'status': ALL_WITH_RELATIONS,
                }


class StaticInterfaceResource(CustomAPIResource):
       
    system = fields.ToOneField(SystemResource, 'system', full=True)
    #system = fields.ForeignKey(SystemResource, 'system', full=True)
    def __init__(self, *args, **kwargs):
        super(StaticInterfaceResource, self).__init__(*args, **kwargs)

    def full_dehydrate(self, bundle):
        super(StaticInterfaceResource, self).full_dehydrate(bundle)
        bundle.obj.update_attrs()
        bundle.data['interface'] = "%s%s.%s" %\
        (bundle.obj.attrs.interface_type,
            bundle.obj.attrs.primary, bundle.obj.attrs.alias)
        del bundle.data['ip_lower']
        del bundle.data['ip_upper']
        del bundle.data['resource_uri']
        return bundle

    class Meta(CustomAPIResource.Meta):
        resource_name = 'interface'
        queryset = StaticInterface.objects.select_related().all()

class OperatingSystemResource(CustomAPIResource):
        
    class Meta(CustomAPIResource.Meta):
        resource_name = 'operating_system'
        queryset = system_model.OperatingSystem.objects.all()
        filtering = {
                'version': ALL_WITH_RELATIONS,
                'name': ALL_WITH_RELATIONS,
                }

class OperatingSystemData(CustomAPIResource):
    resource = "operating_system"

    def get_data(self, data):
        data.set('id', '8')
        data.set('name', 'RHEL')
        data.set('resource_uri', '/tasty/v3/operating_system/8/')
        data.set('version', '6.2')
        return data
class KeyValueResource(CustomAPIResource):
    system = fields.ToOneField('api_v3.system_api.SystemResource', 'system', full=False)

    class Meta(CustomAPIResource.Meta):
        filtering = {
                'system': ALL_WITH_RELATIONS,
                'key': ALL_WITH_RELATIONS,
                'value': ALL_WITH_RELATIONS,
                }
        resource_name = 'key_value'
        queryset = system_model.KeyValue.objects.all()
