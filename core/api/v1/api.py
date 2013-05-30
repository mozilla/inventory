from django.core.exceptions import ValidationError
from tastypie.resources import ModelResource
from tastypie.authorization import Authorization
from tastypie.api import Api
from tastypie import fields
import reversion

from core.network.models import Network
from core.site.models import Site
from core.vlan.models import Vlan
from core.group.models import Group
from core.hwadapter.models import HWAdapter
from core.registration.static.models import StaticReg

from mozdns.api.v1.api import StaticRegResource

import simplejson as json

allowed_methods = ['get', 'post', 'patch', 'delete']
v1_core_api = Api(api_name="v1_core")


class NetworkResource(ModelResource):
    class Meta:
        always_return_data = True
        queryset = Network.objects.all()
        fields = Network.get_api_fields()
        authorization = Authorization()
        allowed_methods = ['get']
        # This model should be RO, update it in the UI


v1_core_api.register(NetworkResource())


class SiteResource(ModelResource):
    class Meta:
        always_return_data = True
        queryset = Site.objects.all()
        fields = Site.get_api_fields()
        authorization = Authorization()
        allowed_methods = ['get']
        # This model should be RO, update it in the UI


v1_core_api.register(SiteResource())


class VlanResource(ModelResource):
    class Meta:
        always_return_data = True
        queryset = Vlan.objects.all()
        fields = Vlan.get_api_fields()
        authorization = Authorization()
        allowed_methods = ['get']
        # This model should be RO, update it in the UI


v1_core_api.register(VlanResource())


class GroupResource(ModelResource):
    class Meta:
        always_return_data = True
        queryset = Group.objects.all()
        fields = Group.get_api_fields()
        authorization = Authorization()
        allowed_methods = ['get']
        # This model should be RO, update it in the UI


v1_core_api.register(GroupResource())


class HWAdapterResource(ModelResource):
    sreg = fields.ToOneField(StaticRegResource, 'sreg', null=False, full=False)
    group = fields.ToOneField(GroupResource, 'group', null=True, full=False)

    def _find_possible(self, bundle, attr, Klass):
        # Do everything possible to find stuff
        possible_pk = bundle.data.get(attr, None)
        if not possible_pk:
            return bundle
        if isinstance(possible_pk, int) or possible_pk.isdigit():
            try:
                bundle.data[attr] = Klass.objects.get(
                    pk=bundle.data[attr]
                )
            except Klass.DoesNotExist:
                pass
        return bundle

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

    def dehydrate(self, bundle):
        if bundle.obj.pk:
            bundle.data['pk'] = bundle.obj.pk
        return bundle

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
