""" Defines the generator function for resource test cases """

from django.test import TestCase
from tastytools.test.resources import TestData
from tastytools.test.client import Client, MultiTestCase, create_multi_meta
from helpers import prepare_test_post_data


def generate(api, setUp=None):
    """ Generates a set of tests for every Resource"""

    if setUp is None:

        def user_setUp(*args, **kwargs):
            return
    else:
        user_setUp = setUp

    class UnderResources(MultiTestCase):
        """ Generates a set of tests for every Resource """

        @staticmethod
        def multi_create_test_resource_unicity(self, resource_name, resource):
            """ verifies that one and only one object of the resource was
            created when calling create_test_resource
            """
            initial_count = len(resource._meta.object_class.objects.all())
            resource.create_test_resource()
            final_count = len(resource._meta.object_class.objects.all())
            self.assertEqual(initial_count + 1, final_count)

        @staticmethod
        def multi_create_test_resource(self, resource_name, resource):
            """ Verifies that the resource's create_test_data method exists and
            it doesn't raise any exceptions when called without any parameters

            """
            try:
                resource.create_test_resource()
            except Exception, err:
                msg = "Could not create test resource for %s" % resource_name
                msg = "%s: %s - %s" % (msg, err.__class__.__name__,
                        err.message)
                self.assertTrue(False, msg)

        @staticmethod
        def multi_test_data_register(self, resource_name, resource):
            """ verify that the resource has a Test Data generating class
            asssociated to it
            """
            if not hasattr(resource._meta, 'testdata'):

                msg = "Missing example data for resource: %(res)s \n"
                msg += "-Did you create a TestData child class for %(res)s?\n"
                msg += "-Did you register the TestData on your Api? \n"
                msg += "-Did you correctly set its resouce='%(res)s' property?"

                msg %= {"res": resource_name}
                self.assertTrue(False, msg)

        @staticmethod
        def multi_testdata_data_existence(self, resource_name, resource):
            """ If a resource allows POST(or GET), this test verifies that
            there is test data for such requests

            """
            #Check existence
            for method in ['POST', 'GET']:
                try:
                    if not hasattr(resource._meta, 'testdata'):
                        msg = "Missing testdata data for resource: %s \n"\
                            "Did you forget to define a TestData class for the\
                            resource?"
                        msg %= (resource_name)
                        self.assertTrue(False, msg)

                    if api.resource_allows_method(resource_name, method):
                        testdata = getattr(resource._meta.testdata,
                            method.lower())
                        msg = "Example %s data is not a TestData or dict "\
                            "but %s"

                        msg %= (method, testdata.__class__)
                        is_testdata = issubclass(testdata.__class__, TestData)
                        is_dict = type(testdata) == dict
                        self.assertTrue(is_testdata or is_dict, msg)

                except (AttributeError, KeyError), err:
                    message = "Missing testdata %s data for %s resource.: %s"
                    message %= (method, resource_name, err)
                    self.assertTrue(False, message)

        @staticmethod
        def multi_test_post(self, resource_name, resource):
            """ If the resource allows POSTing, this test verifies that such
            call using the example post data will work

            """
            if resource.can_create():
                post_data = prepare_test_post_data(self, resource)

                post_response = self.client.post(
                    resource.get_resource_list_uri(), post_data)

                msg = "Failed to POST testdata data for resource %s"\
                    "S: %s. R(%s): %s"
                msg %= (resource_name,
                        post_data,
                        post_response.status_code,
                        post_response.content)
                self.assertEqual(post_response.status_code, 201, msg)

        @staticmethod
        def multi_testdata_get_detail(self, resource_name, resource):
            """ If the resource allows GETing, this test verifies that such
            call returns something similar to the get example data

            """
            if api.resource_allows_detail(resource_name, 'GET'):
                uri, res = resource.create_test_resource()
                get_response = self.client.get(uri, parse='json')
                self.assertEqual(200, get_response.status_code,
                    "Location: %s\nResponse (%s):\n%s" % (
                        uri,
                        get_response.status_code,
                        get_response.data,
                ))
                response_dict = get_response.data

                object_keys = set(response_dict.keys())
                expected_keys = set(resource._meta.testdata.get.keys())

                msg = "GET data does not match the testdata for resource "\
                    "%s - EXAMPLE: %s vs GET: %s"
                msg %= (resource_name, expected_keys, object_keys)
                self.assertEqual(expected_keys, object_keys, msg)

        @staticmethod
        def multi_declared_testdata_fields_coherence(self, resource_name,
            resource):

            #only if resource allows detail GET
            if 'GET' not in resource._meta.detail_allowed_methods:
                return

            testdata_fields = set(resource._meta.testdata_fields)
            declared_fields = set(resource.declared_fields.keys())

            delta = testdata_fields - declared_fields
            if len(delta) > 0:
                msg = "%s.%s field appears on the testdata but it is "\
                    "not declared."
                msg %= (resource_name, delta.pop())
                self.assertTrue(False, msg)

            delta = declared_fields - testdata_fields
            if len(delta) > 0:
                msg = "%s.%s field is declared but is missing from testdata."
                msg %= (resource_name, delta.pop())
                self.assertTrue(False, msg)

        @staticmethod
        def generate_arguments():
            args = []
            for resource_name, resource in api._registry.items():
                if hasattr(resource._meta, "testdata"):
                    args.append((resource_name, resource))
            return args

        @staticmethod
        def generate_test_name(resource_name, resource):
            return resource_name

        @staticmethod
        def setUp(self, test, resource_name, resource):
            test_name = test.__name__
            func_name = test_name.replace("multi_", "setup_")
            self.client = Client()
            if hasattr(resource._meta.testdata, func_name):
                getattr(resource._meta.testdata, func_name)(self)
            user_setUp(self, test_name, resource_name, resource)

    class TestResources(TestCase):
        __metaclass__ = create_multi_meta(UnderResources)

    return TestResources
