from django.core.exceptions import ValidationError
from django.conf.urls.defaults import url

from tastypie.resources import ModelResource
from tastypie.authorization import Authorization
from tastypie.api import Api
from tastypie import fields

from core.network.models import Network
from core.site.models import Site
from core.vlan.models import Vlan
from core.group.models import Group
from core.hwadapter.models import HWAdapter
from core.registration.static.models import StaticReg

from systems.models import (
    System, SystemRack, SystemStatus, SystemType, OperatingSystem, Allocation,
    ServerModel
)

from mozdns.api.v1.api import CommonDNSResource

import reversion

import simplejson as json

allowed_methods = ['get', 'post', 'patch', 'delete']
v1_core_api = Api(api_name="v1_core")


class CoreResource(ModelResource):
    def dehydrate(self, bundle):
        if bundle.obj.pk:
            bundle.data['pk'] = bundle.obj.pk
        return bundle

    def _find_possible(self, bundle, attr, Klass):
        # Do everything possible to find stuff
        possible_pk = bundle.data.get(attr, None)
        if not possible_pk:
            return bundle
        if possible_pk == 'None':
            bundle.data[attr] = None
        elif isinstance(possible_pk, int) or (
                isinstance(possible_pk, str) and
                possible_pk.isdigit()):
            try:
                bundle.data[attr] = Klass.objects.get(
                    pk=bundle.data[attr]
                )
            except Klass.DoesNotExist:
                pass
        return bundle

    def obj_create(self, bundle, request=None, **kwargs):
        return self.save_commit(bundle, request=request, **kwargs)

    def obj_update(self, bundle, request=None, **kwargs):
        return self.save_commit(bundle, request=request, **kwargs)

    def apply_commit(self, obj, commit_data):
        """There *has* to be a more elegant way of doing this."""
        for k, v in commit_data.iteritems():
            if k == 'resource_uri':
                continue
            setattr(obj, k, v)
        return obj

    def save_commit(self, bundle, request=None, **kwargs):
        comment = bundle.data.pop('comment', '')
        bundle = self.full_hydrate(bundle)

        try:
            bundle.obj.full_clean()
            bundle.obj.save()
            reversion.set_comment(comment)
        except ValidationError, e:
            if hasattr(e, 'message_dict'):
                bundle.errors['error_messages'] = json.dumps(e.message_dict)
            else:
                bundle.errors['error_messages'] = json.dumps(
                    e.update_error_dict({})
                )
            self.error_response(bundle.errors, request)
        except Exception, e:
            bundle.errors['error_messages'] = "Very bad error."
            self.error_response(bundle.errors, request)
        return bundle

    class Meta:
        abstract = True
        always_return_data = True
        authorization = Authorization()
        allowed_methods = allowed_methods


class SiteResource(CoreResource):
    parent = fields.ToOneField('self', 'parent', null=True, full=True)

    class Meta:
        always_return_data = True
        queryset = Site.objects.all()
        fields = Site.get_api_fields()
        authorization = Authorization()
        allowed_methods = allowed_methods


v1_core_api.register(SiteResource())


class VlanResource(CoreResource):
    class Meta:
        always_return_data = True
        queryset = Vlan.objects.all()
        fields = Vlan.get_api_fields()
        authorization = Authorization()
        allowed_methods = allowed_methods


v1_core_api.register(VlanResource())


class NetworkResource(CoreResource):
    vlan = fields.ToOneField(VlanResource, 'vlan', null=True, full=True)
    site = fields.ToOneField(SiteResource, 'site', null=True, full=True)

    def hydrate_vlan(self, bundle):
        return self._find_possible(bundle, 'vlan', Vlan)

    def hydrate_site(self, bundle):
        return self._find_possible(bundle, 'site', Site)

    class Meta:
        always_return_data = True
        queryset = Network.objects.all()
        fields = Network.get_api_fields()
        authorization = Authorization()
        allowed_methods = allowed_methods


v1_core_api.register(NetworkResource())


class GroupResource(CoreResource):
    class Meta:
        always_return_data = True
        queryset = Group.objects.all()
        fields = Group.get_api_fields()
        authorization = Authorization()
        allowed_methods = ['get']
        # This model should be RO, update it in the UI


v1_core_api.register(GroupResource())


class ServerModelResource(CoreResource):
    class Meta:
        queryset = ServerModel.objects.all()
        fields = ServerModel.get_api_fields()
        always_return_data = True
        authorization = Authorization()
        allowed_methods = allowed_methods


v1_core_api.register(ServerModelResource())


class AllocationResource(CoreResource):
    class Meta:
        queryset = Allocation.objects.all()
        fields = Allocation.get_api_fields()
        always_return_data = True
        authorization = Authorization()
        allowed_methods = allowed_methods


v1_core_api.register(AllocationResource())


class SystemRackResource(CoreResource):
    site = fields.ToOneField(SiteResource, 'site', null=True, full=True)

    def hydrate_site(self, bundle):
        return self._find_possible(bundle, 'site', Site)

    class Meta:
        queryset = SystemRack.objects.all()
        fields = SystemRack.get_api_fields()
        always_return_data = True
        authorization = Authorization()
        allowed_methods = allowed_methods


v1_core_api.register(SystemRackResource())


class SystemStatusResource(CoreResource):
    class Meta:
        queryset = SystemStatus.objects.all()
        fields = SystemStatus.get_api_fields()
        always_return_data = True
        authorization = Authorization()
        allowed_methods = allowed_methods


v1_core_api.register(SystemStatusResource())


class SystemTypeResource(CoreResource):
    class Meta:
        queryset = SystemType.objects.all()
        fields = SystemType.get_api_fields()
        always_return_data = True
        authorization = Authorization()
        allowed_methods = allowed_methods


v1_core_api.register(SystemTypeResource())


class OperatingSystemResource(CoreResource):
    class Meta:
        queryset = OperatingSystem.objects.all()
        fields = OperatingSystem.get_api_fields()
        always_return_data = True
        authorization = Authorization()
        allowed_methods = allowed_methods


v1_core_api.register(OperatingSystemResource())


class SystemResource(CoreResource):
    server_model = fields.ToOneField(
        ServerModelResource, 'server_model', null=True, full=True
    )

    system_status = fields.ToOneField(
        SystemStatusResource, 'system_status', null=True, full=True
    )

    operating_system = fields.ToOneField(
        OperatingSystemResource, 'operating_system', null=True, full=True
    )

    system_rack = fields.ToOneField(
        SystemRackResource, 'system_rack', null=True, full=True
    )
    allocation = fields.ToOneField(
        AllocationResource, 'allocation', null=True, full=True
    )

    system_type = fields.ToOneField(
        SystemTypeResource, 'system_type', null=True, full=True
    )

    def hydrate_allocation(self, bundle):
        return self._find_possible(bundle, 'allocation', Allocation)

    def hydrate_system_type(self, bundle):
        return self._find_possible(bundle, 'system_type', SystemType)

    def hydrate_server_model(self, bundle):
        return self._find_possible(bundle, 'server_model', ServerModel)

    def hydrate_system_rack(self, bundle):
        return self._find_possible(bundle, 'system_rack', SystemRack)

    def hydrate_operating_system(self, bundle):
        return self._find_possible(bundle, 'operating_system', OperatingSystem)

    def hydrate_system_status(self, bundle):
        return self._find_possible(bundle, 'system_status', SystemStatus)

    def prepend_urls(self):
        """
        Allow a host to be looked up by its hostname
        """
        hostname_target = r'^(?P<resource_name>{0})/(?P<hostname>[\w_.-]+)/$'.format(  # noqa
            self._meta.resource_name
        )
        pk_target = r'^(?P<resource_name>{0})/(?P<pk>[\d]+)/$'.format(
            self._meta.resource_name
        )
        return [
            url(
                pk_target, self.wrap_view('dispatch_detail'),
                name="api_dispatch_detail"
            ),
            url(
                hostname_target, self.wrap_view('dispatch_detail'),
                name="api_dispatch_detail"
            )
        ]

    class Meta:
        queryset = System.objects.all()
        fields = System.get_api_fields()
        always_return_data = True
        authorization = Authorization()
        allowed_methods = allowed_methods


v1_core_api.register(SystemResource())


class StaticRegResource(CommonDNSResource, ModelResource):
    system = fields.ToOneField(SystemResource, 'system', null=False, full=True)
    # Injecting here because of cyclical imports :(
    hwadapter_set = fields.ToManyField(
        'core.api.v1.api.HWAdapterResource', 'hwadapter_set', full=True,
        readonly=True
    )

    def hydrate(self, bundle):
        if 'system_hostname' in bundle.data and 'system' in bundle.data:
            bundle.errors = ("Please only specify a system via the 'system' "
                             "xor the 'system_hostname' parameter")
        if 'system_hostname' in bundle.data:
            system_hostname = bundle.data.get('system_hostname')
            try:
                system = System.objects.get(hostname=system_hostname)
                bundle.data['system'] = system
            except System.DoesNotExist:
                bundle.errors['system'] = (
                    "Couldn't find system with hostname {0}"
                    .format(system_hostname))
        super(StaticRegResource, self).hydrate(bundle)
        return bundle

    def extract_kv(self, bundle):
        """
        This function decides if the POST/PATCH is a trying to add a KV pair to
        the interface. If it is, it makes sure key and value keys are the only
        keys that exist in bundle.data.
        """
        # TODO, rip this out
        kv = []
        if 'key' in bundle.data and 'value' in bundle.data:
            # It's key and value. Nothing else is allowed in the bundle.
            if set('key', 'value') != set(bundle.data):
                error = ("key and value must be the only keys in your "
                         "request when you are updating KV pairs.")
                bundle.errors['keyvalue'] = error
                return []
            else:
                kv.append((bundle.data['key'], bundle.data['value']))
        elif 'key' in bundle.data and 'value' not in bundle.data:
            error = ("When specifying a key you must also specify a value "
                     "for that key")
            bundle.errors['keyvalue'] = error
            return []
        elif 'value' in bundle.data and 'key' not in bundle.data:
            error = ("When specifying a value you must also specify a key "
                     "for that value")
            bundle.errors['keyvalue'] = error
            return []
        return kv

    class Meta:
        always_return_data = True
        queryset = StaticReg.objects.all()
        fields = StaticReg.get_api_fields() + ['views', 'system']
        authorization = Authorization()
        allowed_methods = allowed_methods
        resource_name = 'staticreg'

v1_core_api.register(StaticRegResource())


class HWAdapterResource(CoreResource):
    sreg = fields.ToOneField(StaticRegResource, 'sreg', null=False, full=False)
    group = fields.ToOneField(GroupResource, 'group', null=True, full=False)

    def hydrate_group(self, bundle):
        return self._find_possible(bundle, 'group', Group)

    def hydrate_sreg(self, bundle):
        return self._find_possible(bundle, 'sreg', StaticReg)

    def obj_create(self, bundle, request=None, **kwargs):
        return self.save_commit(bundle, request=request, **kwargs)

    def obj_update(self, bundle, request=None, **kwargs):
        return self.save_commit(bundle, request=request, **kwargs)

    def apply_commit(self, obj, commit_data):
        """There *has* to be a more elegant way of doing this."""
        for k, v in commit_data.iteritems():
            if k == 'resource_uri':
                continue
            setattr(obj, k, v)
        return obj

    def save_commit(self, bundle, request=None, **kwargs):
        comment = bundle.data.pop('comment', '')
        bundle = self.full_hydrate(bundle)
        #self.apply_commit(bundle.obj, bundle.data)
        try:
            bundle.obj.full_clean()
            bundle.obj.save()
            reversion.set_comment(comment)
        except ValidationError, e:
            if hasattr(e, 'message_dict'):
                bundle.errors['error_messages'] = json.dumps(e.message_dict)
            else:
                bundle.errors['error_messages'] = json.dumps(
                    e.update_error_dict({})
                )
            self.error_response(bundle.errors, request)
        except Exception, e:
            bundle.errors['error_messages'] = "Very bad error."
            self.error_response(bundle.errors, request)
        return bundle

    class Meta:
        always_return_data = True
        queryset = HWAdapter.objects.all()
        fields = HWAdapter.get_api_fields() + ['sreg', 'group']
        authorization = Authorization()
        allowed_methods = ['get', 'post', 'patch', 'delete']


v1_core_api.register(HWAdapterResource())
