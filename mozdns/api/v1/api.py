from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import IntegrityError
from tastypie import fields, utils
from tastypie.exceptions import HydrationError
from tastypie.resources import Resource, DeclarativeMetaclass
from tastypie.resources import ModelResource

from systems.models import System
from api_v3.system_api import SystemResource
from core.interface.static_intr.models import StaticInterface
from mozdns.utils import ensure_label_domain, prune_tree
from mozdns.domain.models import Domain
from mozdns.address_record.models import AddressRecord
from mozdns.txt.models import TXT
from mozdns.ptr.models import PTR
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
import re
import traceback
from gettext import gettext as _, ngettext

class CommonDNSResource(ModelResource):
    domain = fields.CharField()
    # User passes string, in hydrate we find a
    # domain
    views = fields.ListField(null=True, blank=True)
    # User passes list of view names, in hydrate we
    # make these the actual view objects

    def obj_delete_list(self, request=None, **kwargs):
        # We dont' want this method being used
        raise NotImplemented


    def dehydrate(self, bundle):
        # Every DNS Resource should have a domain
        bundle.data['views'] = [view.name for view in bundle.obj.views.all()]
        if 'domain' in bundle.data:
            bundle.data['domain'] = bundle.obj.domain.name
        return bundle

    def hydrate(self, bundle):
        """Hydrate handles the conversion of fqdn to a label or domain.
            This function handles two cases:
                1) Label and domain are in bundle
                2) Label and domain are *not* in bundle and fqdn is in bundle.
            All other cases cause hydration errors to be raised and
            bundle.errors will be set.
        """
        # Every DNS Resource should have a domain
        if ('fqdn' not in bundle.data and 'domain' in bundle.data and 'label'
                in bundle.data):
            domain_name = bundle.data.get('domain')
            try:
                domain = Domain.objects.get(name=domain_name)
                bundle.data['domain'] = domain
            except ObjectDoesNotExist, e:
                bundle.errors['domain'] = "Couldn't find domain {0}".format(domain_name)
        elif ('fqdn' in bundle.data and not ('domain' in bundle.data or 'label'
                in bundle.data)):
            try:
                label_domain = ensure_label_domain(bundle.data['fqdn'])
                bundle.data['label'] , bundle.data['domain'] = label_domain
            except ValidationError, e:
                bundle.errors["fqdn"] = e.message
        else:
            error = "Couldn't determine a label and domain for this record."
            bundle.errors['label_and_domain'] = error

        return bundle

    def obj_update(self, bundle, request=None, skip_errors=False, **kwargs):
        obj = bundle.obj
        kv = self.extract_kv(bundle)
        # KV pairs should be saved after the object has been created
        if bundle.errors:
            self.error_response(bundle.errors, request)

        views = self.extract_views(bundle)
        if bundle.errors:
            self.error_response(bundle.errors, request)

        bundle = self.full_hydrate(bundle)

        if bundle.errors:
            self.error_response(bundle.errors, request)
        self.apply_commit(obj, bundle.data)  # bundle should only have valid data.
                                             # If it doesn't errors will be thrown

        return self.save_commit(request, bundle, views, kv)

    def extract_views(self, bundle):
        views = []
        # We have to remove views from data because those need to be added
        # later in a seperate step
        for view_name in bundle.data.pop('views',[]):
            try:
                views.append(View.objects.get(name=view_name))
            except ObjectDoesNotExist, e:
                error = "Couldn't find view {0}".format(view_name)
                bundle.errors['views'] = error
                break
        return views

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

    def obj_create(self, bundle, request=None, **kwargs):
        """
        A generic version of creating a dns object. The strategy is simple: get
        bundle.data to the point where we call Class(**bundle.data) which
        creates an object. We then clean it and then save it. Finally we save
        any views that were in bundle.
        """
        Klass = self._meta.object_class

        kv = self.extract_kv(bundle)
        # KV pairs should be saved after the object has been created
        if bundle.errors:
            self.error_response(bundle.errors, request)

        views = self.extract_views(bundle)
        # views should be saved after the object has been created
        if bundle.errors:
            self.error_response(bundle.errors, request)

        bundle = self.full_hydrate(bundle)
        if bundle.errors:
            self.error_response(bundle.errors, request)



        # Create the Object
        try:
            self.apply_commit(bundle.obj, bundle.data)
        except ValueError, e:
            if 'domain' in bundle.data:
                prune_tree(bundle.data['domain'])
            bundle.errors['error_messages'] = e.message
            self.error_response(bundle.errors, request)
        except TypeError, e:
            if 'domain' in bundle.data:
                prune_tree(bundle.data['domain'])
            bundle.errors['error_messages'] = e.message
            self.error_response(bundle.errors, request)

        return self.save_commit(request, bundle, views, kv)

    def save_commit(self, request, bundle, views, kv):
        try:
            bundle.obj.full_clean()
            bundle.obj.save()
        except ValidationError, e:
            if 'domain' in bundle.data:
                prune_tree(bundle.data['domain'])
            bundle.errors['error_messages'] = str(e)
            self.error_response(bundle.errors, request)
        except Exception, e:
            if 'domain' in bundle.data:
                prune_tree(bundle.data['domain'])
            pdb.set_trace()
            bundle.errors['error_messages'] = "Very bad error."
            self.error_response(bundle.errors, request)

        # We remove the views so that deletion works.
        orig_views = [view for view in bundle.obj.views.all()]
        for view in orig_views:
            bundle.obj.views.remove(view)

        # Now save those views we saved
        for view in views:
            bundle.obj.views.add(view)

        # Now do the kv magic
        if kv:
            bundle.obj.update_attrs()
            for k, v in kv:
                setattr(bundle.obj.attrs, k, v)

        return bundle


allowed_methods = ['get', 'post', 'patch', 'delete']
v1_dns_api = Api(api_name="v1_dns")

class CNAMEResource(CommonDNSResource, ModelResource):
    class Meta:
        always_return_data = True
        queryset = CNAME.objects.all()
        fields = CNAME.get_api_fields() + ['domain', 'views']
        authorization = Authorization()
        allowed_methods = allowed_methods

v1_dns_api.register(CNAMEResource())

class TXTResource(CommonDNSResource, ModelResource):
    class Meta:
        always_return_data = True
        queryset = TXT.objects.all()
        fields = TXT.get_api_fields() + ['domain', 'views']
        authorization = Authorization()
        allowed_methods = allowed_methods

v1_dns_api.register(TXTResource())

class SRVResource(CommonDNSResource, ModelResource):
    class Meta:
        always_return_data = True
        queryset = SRV.objects.all()
        fields = SRV.get_api_fields() + ['domain', 'views']
        authorization = Authorization()
        allowed_methods = allowed_methods

v1_dns_api.register(SRVResource())

class MXResource(CommonDNSResource, ModelResource):
    class Meta:
        always_return_data = True
        queryset = MX.objects.all()
        fields = MX.get_api_fields() + ['domain', 'views']
        authorization = Authorization()
        allowed_methods = allowed_methods

v1_dns_api.register(MXResource())

class SSHFPResource(CommonDNSResource, ModelResource):
    class Meta:
        always_return_data = True
        queryset = SSHFP.objects.all()
        fields = SSHFP.get_api_fields() + ['domain', 'views']
        authorization = Authorization()
        allowed_methods = allowed_methods

v1_dns_api.register(SSHFPResource())

class AddressRecordResource(CommonDNSResource, ModelResource):

    class Meta:
        always_return_data = True
        queryset = AddressRecord.objects.all()
        fields = AddressRecord.get_api_fields() + ['domain', 'views']
        authorization = Authorization()
        allowed_methods = allowed_methods

v1_dns_api.register(AddressRecordResource())

class NameserverResource(CommonDNSResource):
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
            except ObjectDoesNotExist, e:
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

class PTRResource(CommonDNSResource, ModelResource):
    views = fields.ListField(null=True, blank=True)  # User passes list of view names, in hydrate we
                                                    # make these the actual views
    def hydrate(self, bundle):
        # Nothing to do here.
        return bundle

    class Meta:
        always_return_data = True
        queryset = PTR.objects.all()
        fields = PTR.get_api_fields() + ['views']
        authorization = Authorization()
        allowed_methods = allowed_methods

v1_dns_api.register(PTRResource())

class StaticInterfaceResource(CommonDNSResource, ModelResource):
    system = fields.ToOneField(SystemResource, 'system', null=False, full=True)

    def hydrate(self, bundle):
        if 'system_hostname' in bundle.data and 'system' in bundle.data:
            bundle.errors = _("Please only specify a system via the 'system' "
                "xor the 'system_hostname' parameter")
        if 'system_hostname' in bundle.data:
            system_hostname = bundle.data.get('system_hostname')
            try:
                system = System.objects.get(hostname=system_hostname)
                bundle.data['system'] = system
            except ObjectDoesNotExist, e:
                bundle.errors['system'] = _("Couldn't find system with "
                    "hostname {0}".format(system_hostname))
        super(StaticInterfaceResource, self).hydrate(bundle)
        return bundle

    def extract_kv(self, bundle):
        """
        This function decides if the POST/PATCH is a trying to add a KV pair to
        the interface. If it is, it makes sure key and value keys are the only
        keys that exist in bundle.data.

        If there is no key or value in bundle.data this function will attempt
        to decompose KV-ish values (interface_name) into the correct key value
        pairs.
        """
        kv = []
        if 'key' in bundle.data and 'value' in bundle.data:
            # It's key and value. Nothing else is allowed in the bundle.
            if set('key', 'value') != set(bundle.data):
                error = _("key and value must be the only keys in your request "
                    "when you are updating KV pairs.")
                bundle.errors['keyvalue'] = error
                return []
            else:
                kv.append((bundle.data['key'], bundle.data['value']))
        elif 'key' in bundle.data and 'value' not in bundle.data:
            error = _("When specifying a key you must also specify a value for "
                    "that key")
            bundle.errors['keyvalue'] = error
            return []
        elif 'value' in bundle.data and 'key' not in bundle.data:
            error = _("When specifying a value you must also specify a key for "
                    "that value")
            bundle.errors['keyvalue'] = error
            return []
        elif 'iname' in bundle.data:
            iname = re.match("(eth|mgmt)(\d+)\.?(\d+)?", bundle.data['iname'])
            del bundle.data['iname']
            if not iname:
                error = _("Could not parse iname {0} into interface_type and "
                    "primary (or possible not an alias).".format(bundle.data['iname']))
                bundle.errors['iname'] = error
                return []
            kv.append(('interface_type', iname.group(1)))
            kv.append(('primary', iname.group(2)))
            if iname.group(3):
                kv.append(('alias', iname.group(3)))
            else:
                kv.append(('alias', '0'))
        return kv


    class Meta:
        always_return_data = True
        queryset = StaticInterface.objects.all()
        fields = StaticInterface.get_api_fields() + ['domain', 'views', 'system']
        authorization = Authorization()
        allowed_methods = allowed_methods
        resource_name = 'staticinterface'

v1_dns_api.register(StaticInterfaceResource())


"""
class XXXResource(CommonDNSResource, ModelResource):
    class Meta:
        always_return_data = True
        queryset = XXX.objects.all()
        fields = XXX.get_api_fields() + ['domain', 'views']
        authorization = Authorization()
        allowed_methods = allowed_methods

v1_dns_api.register(XXXResource())
"""
