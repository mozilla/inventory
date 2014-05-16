from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import transaction

from tastypie import fields
from tastypie.resources import ModelResource
from tastypie.authorization import Authorization
from tastypie.api import Api

from core.utils import locked_function
from mozdns.utils import ensure_label_domain
from mozdns.domain.models import Domain
from mozdns.address_record.models import AddressRecord
from mozdns.txt.models import TXT
from mozdns.ptr.models import PTR
from mozdns.srv.models import SRV
from mozdns.mx.models import MX
from mozdns.nameserver.models import Nameserver
from mozdns.sshfp.models import SSHFP
from mozdns.cname.models import CNAME
from mozdns.view.models import View


import reversion
import simplejson as json

import traceback


class CommonDNSResource(ModelResource):
    comment = fields.CharField()
    domain = fields.CharField()
    # User passes string, in hydrate we find a
    # domain
    views = fields.ListField(null=True, blank=True)
    # User passes list of view names, in hydrate we
    # make these the actual view objects

    def obj_delete_list(self, request=None, **kwargs):
        # We don't want this method being used
        raise NotImplemented()

    def dehydrate(self, bundle):
        # Most DNS Resources should have a domain and a fqdn and some views
        bundle.data['views'] = [view.name for view in bundle.obj.views.all()]
        if 'domain' in bundle.data:
            bundle.data['domain'] = bundle.obj.domain.name
        if bundle.obj.pk:
            bundle.data['pk'] = bundle.obj.pk
        bundle.data['meta'] = {}
        if bundle.obj.domain and bundle.obj.domain.soa:
            bundle.data['meta']['soa'] = str(bundle.obj.domain.soa)
        if hasattr(bundle.obj, 'fqdn'):
            bundle.data['meta']['fqdn'] = bundle.obj.fqdn
        return bundle

    def hydrate(self, bundle):
        """Hydrate handles the conversion of fqdn to a label or domain."""
        if 'fqdn' in bundle.data:
            try:
                label_domain = ensure_label_domain(bundle.data['fqdn'])
                bundle.data['label'], bundle.data['domain'] = label_domain
            except ValidationError, e:
                errors = {}
                errors['fqdn'] = e.messages
                bundle.errors['error_messages'] = json.dumps(errors)
                # We should use an Error(Dict|List) to maintain consistency
                # with the errors that are thrown by full_clean.
        else:
            errors = {}
            errors['fqdn'] = ("Couldn't determine a label and "
                              "domain for this record.")
            bundle.errors['error_messages'] = json.dumps(errors)

        if 'ttl' in bundle.data and bundle.data['ttl'] == 'None':
            bundle.data['ttl'] = None

        return bundle

    @transaction.commit_on_success
    def obj_update(self, bundle, request=None, skip_errors=False, **kwargs):
        """
        When an object is being updated it is possible to update the label
        and domain of a resource with the 'fqdn' keyword.  During hydrate, the
        correct label and domain will be chosen so the object ends up with a
        matching fqdn. By default, tastypie will populate bundle.data with an
        object's current state, which causes label, domain, and fqdn to all be
        in bundle.data. If the 'fqdn' keyword exists the keys 'label' and
        'domain' will be removed from the bundle before hydrate is called.
        """
        # Note, error_response() raises an ImmediateHttpResponse exception.
        # This should trigger transaction.commit_on_success to rollback what
        # happens in this function

        # KV pairs should be saved after the object has been created
        kv = self.extract_kv(bundle)

        if bundle.errors:
            self.error_response(bundle.errors, request)

        views = bundle.data.pop('views', [])
        comment = bundle.data.pop('comment', '')

        bundle = self.full_hydrate(bundle)

        if bundle.errors:
            self.error_response(bundle.errors, request)

        self.apply_commit(bundle.obj, bundle.data)

        return self.save_commit(request, bundle, views, comment, kv)

    def update_views(self, obj, views):
        # We have to remove views from data because those need to be added
        # later in a seperate step
        public_view = View.objects.get(name='public')
        private_view = View.objects.get(name='private')
        view_set = set(obj.views.all())
        for view_name in views:
            if view_name == 'no-public' and public_view in view_set:
                view_set.remove(public_view)
            elif view_name == 'public':
                view_set.add(public_view)
            if view_name == 'no-private' and private_view in view_set:
                view_set.remove(private_view)
            elif view_name == 'private':
                view_set.add(private_view)

        obj.clean_views(view_set)
        for view in View.objects.all():
            if view not in view_set:
                obj.views.remove(view)
            else:
                obj.views.add(view)

    def extract_kv(self, bundle):
        return []

    def apply_commit(self, obj, commit_data):
        """There *has* to be a more elegant way of doing this."""
        for k, v in commit_data.iteritems():
            if k == 'resource_uri':
                continue
            if k == 'system':
                continue
            setattr(obj, k, v)
        return obj

    @transaction.commit_on_success
    def obj_create(self, bundle, request=None, **kwargs):
        """
        A generic version of creating a dns object. The strategy is simple: get
        bundle.data to the point where we call Class(**bundle.data) which
        creates an object. We then clean it and then save it. Finally we save
        any views that were in the bundle.
        """
        # Note, error_response() raises an ImmediateHttpResponse exception.
        # This should trigger transaction.commit_on_success to rollback what
        # happens in this function

        kv = self.extract_kv(bundle)
        # KV pairs should be saved after the object has been created
        if bundle.errors:
            self.error_response(bundle.errors, request)

        views = bundle.data.pop('views', [])
        comment = bundle.data.pop('comment', '')
        # views should be saved after the object has been created
        if bundle.errors:
            self.error_response(bundle.errors, request)

        bundle = self.full_hydrate(bundle)
        if bundle.errors:
            self.error_response(bundle.errors, request)

        # Create the Object
        try:
            self.apply_commit(bundle.obj, bundle.data)
        except (ValueError, TypeError), e:
            bundle.errors['error_messages'] = e.message
            self.error_response(bundle.errors, request)

        return self.save_commit(request, bundle, views, comment, kv)

    @locked_function('inventory.record_lock')
    def save_commit(self, request, bundle, views, comment, kv):
        verb = "updated" if bundle.obj.pk else "created"
        error = None
        try:
            # obj's save() method should be calling full_clean()
            bundle.obj.save()
        except ValidationError, e:
            error = json.dumps(e.message_dict)
        except Exception, e:
            error = "Please report this error: {0}".format(
                traceback.format_exc()
            )

        if error:
            bundle.errors['error_messages'] = error
            self.error_response(bundle.errors, request)

        reversion.set_comment(comment)
        if request.user.is_authenticated():
            reversion.set_user(request.user)

        try:
            self.update_views(bundle.obj, views)
            # Now do the kv magic
            if kv:
                bundle.obj.update_attrs()
                for k, v in kv:
                    setattr(bundle.obj.attrs, k, v)
        except ValidationError, e:
            bundle.data['error_messages'] = {'views': (
                "Some views failed validation with the message: {0}. "
                "The object was not" "{1}".format(e.messages[0], verb)
            )}
            self.error_response(bundle.errors, request)

        return bundle


allowed_methods = ['get', 'post', 'patch', 'delete']
v1_dns_api = Api(api_name="v1_dns")


class ObjectListMixin(ModelResource):
    """We need a way to take a django Q, make a query with it, and then lower
    the objects returned by the query into tastypie resources.
    """

    def model_to_data(self, model, request=None):
        # joshbohde++
        bundle = self.build_bundle(obj=model, request=request)
        return self.full_dehydrate(bundle).data


class CNAMEResource(CommonDNSResource, ObjectListMixin, ModelResource):
    class Meta:
        always_return_data = True
        queryset = CNAME.objects.all()
        fields = CNAME.get_api_fields() + ['views']
        authorization = Authorization()
        allowed_methods = allowed_methods


v1_dns_api.register(CNAMEResource())


class TXTResource(CommonDNSResource, ObjectListMixin, ModelResource):
    class Meta:
        always_return_data = True
        queryset = TXT.objects.all()
        fields = TXT.get_api_fields() + ['views']
        authorization = Authorization()
        allowed_methods = allowed_methods


v1_dns_api.register(TXTResource())


class SRVResource(CommonDNSResource, ObjectListMixin, ModelResource):
    class Meta:
        always_return_data = True
        queryset = SRV.objects.all()
        fields = SRV.get_api_fields() + ['views']
        authorization = Authorization()
        allowed_methods = allowed_methods


v1_dns_api.register(SRVResource())


class MXResource(CommonDNSResource, ObjectListMixin, ModelResource):
    class Meta:
        always_return_data = True
        queryset = MX.objects.all()
        fields = MX.get_api_fields() + ['views']
        authorization = Authorization()
        allowed_methods = allowed_methods


v1_dns_api.register(MXResource())


class SSHFPResource(CommonDNSResource, ObjectListMixin, ModelResource):
    class Meta:
        always_return_data = True
        queryset = SSHFP.objects.all()
        fields = SSHFP.get_api_fields() + ['views']
        authorization = Authorization()
        allowed_methods = allowed_methods


v1_dns_api.register(SSHFPResource())


class AddressRecordResource(CommonDNSResource, ObjectListMixin, ModelResource):
    class Meta:
        always_return_data = True
        queryset = AddressRecord.objects.all()
        fields = AddressRecord.get_api_fields() + ['views']
        authorization = Authorization()
        allowed_methods = allowed_methods


v1_dns_api.register(AddressRecordResource())


class NameserverResource(CommonDNSResource, ObjectListMixin):
    def hydrate(self, bundle):
        # Nameservers don't have a label
        if 'fqdn' in bundle.data:
            bundle.errors['domain'] = "Nameservers shouldn't have a fqdn"
        elif 'label' in bundle.data:
            bundle.errors['domain'] = "Nameservers shouldn't have a label"
        else:
            domain_name = bundle.data.get('domain', '')
            try:
                domain = Domain.objects.get(name=domain_name)
                bundle.data['domain'] = domain
            except ObjectDoesNotExist:
                error = "Couldn't find domain {0}".format(domain_name)
                bundle.errors['domain'] = error
        return bundle

    class Meta:
        always_return_data = True
        queryset = Nameserver.objects.all()
        fields = Nameserver.get_api_fields() + ['domain', 'views']
        authorization = Authorization()
        allowed_methods = allowed_methods


v1_dns_api.register(NameserverResource())


class PTRResource(CommonDNSResource, ObjectListMixin, ModelResource):
    views = fields.ListField(null=True, blank=True)
    # User passes list of view names, in hydrate we
    # make these the actual views

    def hydrate(self, bundle):
        # Nothing to do here.
        return bundle

    def dehydrate(self, bundle):
        bundle.data['views'] = [view.name for view in bundle.obj.views.all()]
        # Don't clobber the actual reverse_domain field
        # If this 'ptr_reverse_domain' is called 'reverse_domain', tastypie
        # will try to serialize this field to a reverse_domain object (we don't
        # want that).
        bundle.data['meta'] = {}
        bundle.data['meta']['reverse_domain'] = bundle.obj.reverse_domain.name
        if bundle.obj.reverse_domain.soa:
            bundle.data['meta']['soa'] = str(bundle.obj.reverse_domain.soa)
        if bundle.obj.pk:
            bundle.data['pk'] = bundle.obj.pk
        return bundle

    class Meta:
        always_return_data = True
        queryset = PTR.objects.all()
        fields = PTR.get_api_fields() + ['views']
        authorization = Authorization()
        allowed_methods = allowed_methods


v1_dns_api.register(PTRResource())


"""
class XXXResource(CommonDNSResource, ObjectListMixin, ModelResource):
    class Meta:
        always_return_data = True
        queryset = XXX.objects.all()
        fields = XXX.get_api_fields() + ['domain', 'views']
        authorization = Authorization()
        allowed_methods = allowed_methods

v1_dns_api.register(XXXResource())
"""
