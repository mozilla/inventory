from tastypie.api import Api as TastyApi
from tastypie.resources import Resource as TastyResource, ModelResource as TastyModelResource
from tastytools.resources import ModelResource as ToolsModelResource, Resource as ToolsResource
from tastytools.test.resources import ResourceTestData
import json
import inspect


def _resources_from_module(module):
    for name in dir(module):
        o = getattr(module, name)
        try:
            base_classes = [ToolsResource, ToolsModelResource, TastyResource, TastyModelResource]
            is_base_class = o in base_classes
            is_resource_class =  issubclass(o, TastyResource)

            if is_resource_class and not is_base_class:
                yield o
        except TypeError: pass

def _testdata_from_module(module):
    for name in dir(module):
        o = getattr(module, name)
        try:
            base_classes = [ResourceTestData]
            is_base_class = o in base_classes
            is_testdata_class =  issubclass(o, ResourceTestData)

            if is_testdata_class and not is_base_class:
                yield o
        except TypeError: pass


class Api(TastyApi):

    _testdata = {}

    def resource(self, resource_name):
        return self._registry[resource_name]

    def register(self, resource=None, canonical=True, **kwargs):
        resource_list = []

        if resource is not None:
            resource_list.append(resource)
        if 'resources' in kwargs:
            resource_list += kwargs['resources']
        if 'modules' in kwargs:
            for module in kwargs['modules']:
                resource_list += _resources_from_module(module)

        for resource in resource_list:
            if inspect.isclass(resource):
                resource = resource()

            super(Api, self).register(resource, canonical)
            self._bind_testdata(resource._meta.resource_name)

    def register_testdata(self, testdata=None, **kwargs):
        testdata_list = []

        if testdata is not None:
            testdata_list.append(testdata)
        if 'list' in kwargs:
            testdata_list += kwargs['list']
        if 'modules' in kwargs:
            for module in kwargs['modules']:
                testdata_list += _testdata_from_module(module)

        for testdata in testdata_list:
            if inspect.isclass(testdata):
                testdata = testdata(self)
            resource_name = testdata.__class__.resource
            self._testdata[resource_name] = testdata
            self._bind_testdata(resource_name)

    def _bind_testdata(self, resource_name):
        testdata = self._testdata.get(resource_name)
        resource = self._registry.get(resource_name)

        if testdata is None:
            return
        if resource is None:
            return

        resource._meta.testdata = testdata

    def get_resource_example_data(self, resource_name, method):
        return getattr(self.resource(resource_name)._meta.testdata,
            method.lower())

    def resource_allows_method(self, resource_name, method):
        options = self.resource(resource_name)._meta
        allowed = set(options.allowed_methods + options.detail_allowed_methods)
        return method.lower() in allowed

    def resource_allows_detail(self, resource_name, method):
        options = self.resource(resource_name)._meta
        return method.lower() in options.detail_allowed_methods


    def dehydrate(self, resource, obj, request=None):
        if type(resource) is str:
            resource = self.resource(resource)
        bundle = resource.build_bundle(obj=obj, request=request)
        bundle = resource.full_dehydrate(bundle)
        return json.loads(resource.serialize(None, bundle, 'application/json'))
