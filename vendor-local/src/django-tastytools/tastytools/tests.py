from django.test import TestCase
from django.test.client import RequestFactory
from api import Api
from example import resources1, resources2, resources3
from example import testdata1
from validation import FieldsValidation
from test.client import Client
from models import Test as TestModel
from django.core.urlresolvers import reverse
from tastytools.test.resources import ResourceTestData


class ApiTestCase(TestCase):
    urls = 'tastytools.test_urls'
    
    def setUp(self):
        self.api = Api()
        
    def _assert_in_registry(self, resource_names):
        for resource_name in resource_names:
            try:
                assert resource_name in self.api._registry 
            except:
                print resource_name
                raise

    def test_resource_importing(self):
        """The Api class is able to import a single resource"""
        self.api.register(resources1.Test_1_1_Resource())
        self._assert_in_registry(["test_1_1"])

    def test_resource_list_importing(self):
        """The Api class is able to import a list of resources"""
        resources = [
                resources1.Test_1_2_Resource, 
                resources1.Test_1_3_Resource() 
            ]
        self.api.register(resources=resources)
        self._assert_in_registry(["test_1_2", "test_1_3"])
        
    def test_module_list_importing(self):
        """The Api class is able to import all resources from listed modules"""
        modules = [resources2, resources3]
        self.api.register(modules=modules)
        self._assert_in_registry(["test_2_1", "test_2_2", "test_2_3"])
        self._assert_in_registry(["test_3_1", "test_3_2", "test_3_3"])
        
    def test_testdata(self):
        """The API is able to register a testdata class"""
        self.api.register(resources1.Test_1_1_Resource())
        self.api.register_testdata(testdata1.Test_1_1_TestData)
        td = self.api.resource("test_1_1")._meta.testdata
        msg = "%s is not subclass of ResourceTestData" % td.__class__
        self.assertTrue(issubclass(td.__class__, ResourceTestData), msg)
        res = self.api.resource("test_1_1").create_test_resource()

    def test_testdata_list(self):
        """The API is able to register a list of testdata classes"""
        resources=[resources1.Test_1_1_Resource(), resources1.Test_1_2_Resource()]
        self.api.register(resources=resources)
        testdata_list=[testdata1.Test_1_1_TestData,testdata1.Test_1_2_TestData]
        self.api.register_testdata(list=testdata_list)
        
        for r in ["test_1_1", "test_1_2"]:
            td = self.api.resource(r)._meta.testdata
            msg = "%s is not subclass of ResourceTestData" % td.__class__
            self.assertTrue(issubclass(td.__class__, ResourceTestData), msg)
            res = self.api.resource(r).create_test_resource()

    def test_testdata_modules(self):
        """The API is able to register a testdata classes from a module"""
        self.api.register(modules=[resources1])
        self.api.register_testdata(modules=[testdata1])

        for r in ["test_1_1", "test_1_2"]:
            td = self.api.resource(r)._meta.testdata
            msg = "%s is not subclass of ResourceTestData" % td.__class__
            self.assertTrue(issubclass(td.__class__, ResourceTestData), msg)
            res = self.api.resource(r).create_test_resource()


class ClientTest(TestCase):
    urls = 'tastytools.test_urls'
    
    def test_urls_are_working(self):
        self.assertEqual("/test", reverse("test_url"))
    
    def test_path_or_resource(self):
        c = Client()
        obj = TestModel()
        obj.test = 'TESTING'
        obj.save()
        
        resource = resources1.Test_1_1_Resource()
        
        list_path = resource.get_resource_list_uri()
        object_path = resource.get_resource_uri(obj)
        
        result = c._path_or_resource(list_path)
        expected = list_path
        self.assertEqual(result, expected, 
            "Bare path.\nResult:%s\nExpected:%s" % (result, expected))
            
        result = c._path_or_resource(list_path, obj)
        expected = list_path
        self.assertEqual(result, expected, 
            "Bare path w/obj.\nResult:%s\nExpected:%s" % (result, expected))
            
        result = c._path_or_resource(resource)
        expected = list_path
        self.assertEqual(result, expected, 
            "Empty resource.\nResult:%s\nExpected:%s" % (result, expected))
            
        result = c._path_or_resource(resource, obj)
        expected = object_path
        self.assertEqual(result, expected, 
            "Populated resource.\nResult:%s\nExpected:%s" % (result, expected))            
            
            
class FieldsValidationTest(TestCase):
    def test_parse_methods_key(self):
        validation = FieldsValidation()
        key = "required_post"
        #value = ['field1', 'field2']

        methods = validation.parse_methods_key(key, 'required')
        self.assertEqual(['POST'], methods)

    def test_map_method_validation(self):
        validation = FieldsValidation()
        fields = ['field1', 'field2']
        methods = ["POST", "PUT", "GET", "DELETE"]
        target = {}
        validation.map_method_validations(target, fields, methods)

        expected = {
                'POST': ['field1', 'field2'],
                'GET': ['field1', 'field2'],
                'PUT': ['field1', 'field2'],
                'DELETE': ['field1', 'field2'],
                }

        self.assertEqual(expected, target)

        validation.map_method_validations(target, ['field3'], ['PUT', 'POST'])

        expected = {
                'POST': ['field1', 'field2', 'field3'],
                'GET': ['field1', 'field2'],
                'PUT': ['field1', 'field2', 'field3'],
                'DELETE': ['field1', 'field2'],
                }

        self.assertEqual(expected, target)

    def test_fieldsvalid_constructor(self):
        validation = FieldsValidation(required=['f1', 'f2'],
                                      validated=['f1', 'f3'],
                                      required_post_get=['f4'],
                                      validated_put=['f5'])

        expected_required = {
                'POST': ['f1', 'f2', 'f4'],
                'GET': ['f1', 'f2', 'f4'],
                'PUT': ['f1', 'f2'],
                'DELETE': ['f1', 'f2'],
                'PATCH': ['f1', 'f2'],
                }

        expected_validated = {
                'POST': ['f1', 'f3'],
                'GET': ['f1', 'f3'],
                'PUT': ['f1', 'f3', 'f5'],
                'DELETE': ['f1', 'f3'],
                'PATCH': ['f1', 'f3'],
                }

        self.assertEqual(expected_validated, validation.validated_fields)
        self.assertEqual(expected_required, validation.required_fields)
