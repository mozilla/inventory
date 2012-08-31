from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import IntegrityError
from tastypie import fields, utils
from tastypie.exceptions import HydrationError
from tastypie.resources import Resource, DeclarativeMetaclass
from tastypie.resources import ModelResource
from mozdns.domain.models import Domain
from mozdns.address_record.models import AddressRecord
from mozdns.txt.models import TXT
from mozdns.srv.models import SRV
from mozdns.mx.models import MX
from mozdns.nameserver.models import Nameserver
from mozdns.sshfp.models import SSHFP
from mozdns.txt.forms import TXTForm
from mozdns.cname.models import CNAME
from mozdns.cname.forms import CNAMEForm
from mozdns.domain.forms import DomainForm
from mozdns.view.models import View
from tastypie.validation import FormValidation

from tastypie.authorization import Authorization

from tastypie.api import Api

import pdb
import sys
import traceback

class CommonDNSResource(Resource):
    domain = fields.CharField()  # User passes string, in hydrate we find a
                                 # domain
    views = fields.ListField(null=True, blank=True)  # User passes list of view names, in hydrate we
                                # make these the actual views

    def dehydrate(self, bundle):
        # Every DNS Resource should have a domain
        bundle.data['views'] = [view.name for view in bundle.obj.views.all()]
        bundle.data['domain'] = bundle.obj.domain.name
        return bundle

    def hydrate_m2m(self, bundle):
        for view_name in bundle.data['views']:
            try:
                view = View.objects.get(name=view_name)
            except ObjectDoesNotExist, e:
                raise HydrationError("Couldn't find the view "
                        "{0}".format(view_name))
        return bundle

    def hydrate(self, bundle):
        # Every DNS Resource should have a domain
        domain_name = bundle.data.get('domain', '')
        try:
            domain = Domain.objects.get(name=domain_name)
        except ObjectDoesNotExist, e:
            raise HydrationError("Couldn't find domain "
                    "{0}".format(domain_name))
        bundle.data['domain'] = domain
        return bundle

    def obj_update(self, bundle, request=None, skip_errors=False, **kwargs):
        obj = bundle.obj
        views = self.extract_views(bundle)
        bundle = self.full_hydrate(bundle)

        if bundle.errors:
            self.error_response(bundle.errors, request)
        self.apply_commit(obj, bundle.data)  # bundle should only have valid data.
                                                   # If it doesn't errors will be thrown
        self.apply_custom_hydrate(obj, bundle, action='update')
        return self.save_commit(request, obj, bundle, views)

    def extract_views(self, bundle):
        views = []
        # We have to remove views from data because those need to be added
        # later in a seperate step
        for view_name in bundle.data.pop('views',[]):
            try:
                views.append(View.objects.get(name=view_name))
            except ObjectDoesNotExist, e:
                raise HydrationError("Couldn't find the view "
                        "{0}".format(view_name))
        return views

    def apply_commit(self, obj, commit_data):
        for k, v in commit_data.iteritems():
            if k == 'resource_uri':
                continue
            setattr(obj, k, v)
        return obj

    def obj_create(self, bundle, request=None, **kwargs):
        """
        A generic version of creating a dns object. The strategy is simple: get
        bundle.data to the point where we call Class(**bundle.data) which
        creates an object. We then clean it and then save it. Finally we save
        any views that were in bundle.
        """

        Klass = self._meta.object_class
        views = self.extract_views(bundle)
        bundle = self.full_hydrate(bundle)

        if bundle.errors:
            self.error_response(bundle.errors, request)

        # Create the Object
        try:
            obj = Klass(**bundle.data)
        except ValueError, e:
            pdb.set_trace()
        except TypeError, e:
            bundle.errors['error_messages'] = e.message
            self.error_response(bundle.errors, request)

        return self.save_commit(request, obj, bundle, views)

    def save_commit(self, request, obj, bundle, views):
        try:
            obj.full_clean()
        except ValidationError, e:
            bundle.errors['error_messages'] = str(e)
            self.error_response(bundle.errors, request)
        except Exception, e:
            pdb.set_trace()
        obj.save()

        # We remove the views so that deletion works.
        orig_views = [view for view in obj.views.all()]
        for view in orig_views:
            obj.views.remove(view)

        for view in views:
            obj.views.add(view)

        # Now save those views we saved
        bundle.obj = obj
        return bundle

    def apply_custom_hydrate(self, obj, bundle, action=None):
        return bundle


allowed_methods = ['get', 'post', 'patch', 'delete']
v1_dns_api = Api(api_name="v1_dns")

class CNAMEResource(CommonDNSResource, ModelResource):
    class Meta:
        queryset = CNAME.objects.all()
        fields = CNAME.get_api_fields() + ['domain', 'views']
        authorization = Authorization()
        allowed_methods = allowed_methods

v1_dns_api.register(CNAMEResource())

class TXTResource(CommonDNSResource, ModelResource):
    class Meta:
        queryset = TXT.objects.all()
        fields = TXT.get_api_fields() + ['domain', 'views']
        authorization = Authorization()
        allowed_methods = allowed_methods
v1_dns_api.register(TXTResource())

class SRVResource(CommonDNSResource, ModelResource):
    class Meta:
        queryset = SRV.objects.all()
        fields = SRV.get_api_fields() + ['domain', 'views']
        authorization = Authorization()
        allowed_methods = allowed_methods
v1_dns_api.register(SRVResource())

class MXResource(CommonDNSResource, ModelResource):
    class Meta:
        queryset = MX.objects.all()
        fields = MX.get_api_fields() + ['domain', 'views']
        authorization = Authorization()
        allowed_methods = allowed_methods
v1_dns_api.register(MXResource())

class SSHFPResource(CommonDNSResource, ModelResource):
    class Meta:
        queryset = SSHFP.objects.all()
        fields = SSHFP.get_api_fields() + ['domain', 'views']
        authorization = Authorization()
        allowed_methods = allowed_methods
v1_dns_api.register(SSHFPResource())

class AddressRecordResource(CommonDNSResource, ModelResource):

    class Meta:
        queryset = AddressRecord.objects.all()
        fields = AddressRecord.get_api_fields() + ['domain', 'views']
        authorization = Authorization()
        allowed_methods = allowed_methods

v1_dns_api.register(AddressRecordResource())

"""
class XXXResource(CommonDNSResource, ModelResource):
    class Meta:
        queryset = XXX.objects.all()
        fields = XXX.get_api_fields() + ['domain', 'views']
        authorization = Authorization()
        allowed_methods = allowed_methods
v1_dns_api.register(XXXResource())
"""

