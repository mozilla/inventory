from tastypie.resources import Resource as TastyResource
from tastypie.resources import ModelResource as TastyModelResource
from django.conf.urls.defaults import url
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from tastytools import fields
from test.resources import TestData
from django.http import HttpResponse
from django.utils import simplejson
from tastypie import http
from tastytools.authentication import AuthenticationByMethod
from tastypie.authentication import Authentication
from tastypie.exceptions import ImmediateHttpResponse
from tastypie.utils import trailing_slash

import inspect


class Resource(TastyResource):
    resource_uri = fields.CharField(help_text='URI of the resource.',
        readonly=True)


class ModelResource(TastyModelResource):

    resource_uri = fields.CharField(help_text='URI of the resource.',
        readonly=True)

    def __init__(self, *args, **kwargs):
        super(ModelResource, self).__init__(*args, **kwargs)
        for field_name, field_object in self.fields.items():
            if field_name in getattr(self._meta, "uploads", []):
                field_object.readonly = True

    def IHR(self, response_class, data, request=None):
        return ImmediateHttpResponse(self.create_response(
            request, data, response_class))

    def save_m2m(self, bundle):
        """
        Handles the saving of related M2M data.

        Due to the way Django works, the M2M data must be handled after the
        main instance, which is why this isn't a part of the main
        ``save`` bits.

        Currently slightly inefficient in that it will clear out the whole
        relation and recreate the related data as needed.
        """
        for field_name, field_object in self.fields.items():
            if not getattr(field_object, 'is_m2m', False):
                continue

            if not field_object.attribute:
                continue

            if field_object.readonly:
                continue

            if inspect.isfunction(field_object.attribute):
                continue
            # Get the manager.
            related_mngr = getattr(bundle.obj, field_object.attribute)

            if hasattr(related_mngr, 'clear'):
                # Clear it out, just to be safe.
                related_mngr.clear()

            related_objs = []

            for related_bundle in bundle.data[field_name]:
                related_bundle.obj.save()
                related_objs.append(related_bundle.obj)

            if not hasattr(related_mngr, 'add'):
                func = "save_m2m_%s" % field_name
                if not hasattr(self, func):
                    msg = "Missing save ManyToMany related %s function: %s."
                    msg %= (field_name, func)
                    raise Exception(msg)
                getattr(self, func)(bundle, related_objs)
            else:
                related_mngr.add(*related_objs)

    def apply_authorization_limits(self, request, object_list):
        if request is not None and request.method in ['PUT', 'PATCH']:
            json_data = simplejson.loads(request.raw_post_data)
            for key in json_data.keys():
                fld = self.fields.get(key, None)
                if fld is not None and getattr(fld, "final", False):
                    response = http.HttpUnauthorized("Error message")
                    raise ImmediateHttpResponse(response=response)
        return object_list

    def method_requires_auth(self, method):
        if isinstance(self._meta.authentication, AuthenticationByMethod):
            anon_methods = self._meta.authentication.allowed_methods
        elif isinstance(self._meta.authentication, Authentication):
            anon_methods = self._meta.allowed_methods
        else:
            anon_methods = []

        if method in anon_methods:
            return False
        else:
            return True

    def can_patch(self):
        """
        Checks to ensure ``patch`` is within ``allowed_methods``.

        Used when hydrating related data.
        """
        list_allowed = self._meta.list_allowed_methods
        detail_allowed = self._meta.detail_allowed_methods
        allowed = set(list_allowed + detail_allowed)

        return 'patch' in allowed

    def base_urls(self):
        urls = []

        urlexp = r'^(?P<resource_name>%s)/example/'
        urlexp %= self._meta.resource_name
        urls.append(url(urlexp, self.wrap_view('get_testdata_data_view'),
                name='get_testdata_data_view'))

        urlexp_2 = r'^(?P<resource_name>%s)/schema/'
        urlexp_2 %= self._meta.resource_name
        urls.append(url(urlexp_2, self.wrap_view('get_doc_data_view'),
                name='api_get_doc_data'))

        upload_url = r"^(?P<resource_name>%s)/(?P<pk>\w[\w/-]*)/attach%s$"
        upload_url %= (self._meta.resource_name, trailing_slash())
        urls.append(url(upload_url, self.wrap_view("attach_upload"),
                name="api_attach_upload"))

        urls += super(ModelResource, self).base_urls()
        return urls

    def attach_upload(self, request, resource_name, pk, **kwargs):
        """Attaches uploaded files to the resource"""

        try:
            obj = self.cached_obj_get(
                    request=request, pk=pk,
                    **self.remove_api_resource_names(kwargs))
        except ObjectDoesNotExist:
            return http.HttpNotFound()
        except MultipleObjectsReturned:
            return http.HttpMultipleChoices(
                    "More than one resource is found at this URI.")

        for field_name in getattr(self._meta, "uploads", []):
            uploaded_file = request.FILES.get(field_name, None)
            if uploaded_file is not None:
                setattr(obj, field_name, uploaded_file)
        obj.save()
        bundle = self.build_bundle(obj=obj, request=request)
        bundle = self.full_dehydrate(bundle)
        bundle = self.alter_detail_data_to_serialize(request, bundle)
        return self.create_response(request, bundle, http.HttpAccepted)

    def create_test_resource(self, force=False, *args, **kwargs):

        force = force or {}
        try:
            return self._meta.testdata.create_test_resource(force=force, *args,
                **kwargs)
        except AttributeError as e:
            msg = "%s: Did you forget to define a testdata class for %s?"
            msg %= (e, self.__class__.__name__)
            raise Exception(msg)

    def create_test_model(self, data=None, *args, **kwargs):
        if data is None:
            data = {}

        return self._meta.testdata.create_test_model(data, *args, **kwargs)

    def get_test_post_data(self, data=None):
        if data is None:
            data = {}

        #print "getting post data from %s" % self._meta.testdata
        out = self._meta.testdata.post
        if isinstance(out, TestData):
            out = out.data

        return out

    def get_testdata_data_view(self, request, api_name=None,
        resource_name=None):

        if self._meta.testdata is not None:
            output = {
                    'POST': self._meta.testdata.post,
                    'GET': self._meta.testdata.get
            }

            requested_type = request.GET.get('type', 'False')
            try:
                output = output[requested_type.upper()]
            except KeyError:
                pass
            response_class = HttpResponse
        else:
            output = {
                    'error': 'missing api'
            }
            response_class = http.HttpBadRequest

        return self.create_response(request, output,
            response_class=response_class)

    def get_doc_data_view(self, request, api_name=None,
        resource_name=None):

            allowed_methods = self._meta.allowed_methods
            if isinstance(self._meta.authentication, AuthenticationByMethod):
                anon_methods = self._meta.authentication.allowed_methods
            elif isinstance(self._meta.authentication, Authentication):
                anon_methods = allowed_methods
            else:
                anon_methods = []

            schema = self.build_schema()
            methods = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']
            authentication_list = {}

            for method in methods:
                if method.lower() not in allowed_methods:
                    authentication_list[method.lower()] = 'NOT_ALLOWED'
                elif method in anon_methods:
                    authentication_list[method.lower()] = 'ALLOWED'
                else:
                    authentication_list[method.lower()] = 'AUTH_REQUIRED'

            schema['auth'] = authentication_list
            for key, value in schema['fields'].items():
                schema['fields'][key]['final'] = value.get('final', False)
            return self.create_response(request, schema)
