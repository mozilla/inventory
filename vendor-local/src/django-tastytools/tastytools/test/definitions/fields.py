""" Defines the generator function for field test cases """

from django.test import TestCase
from tastytools.test.client import Client, MultiTestCase, create_multi_meta
from datetime import datetime
from helpers import prepare_test_post_data
import random


class FieldNotSupportedException(Exception):
    pass


def generate(api, setUp=None):
    """ Generates a set of tests for every Field of every Resource"""
    if setUp is None:

        def user_setUp(*args, **kwargs):
            return
    else:
        user_setUp = setUp

    class UnderResourceFields(MultiTestCase):
        """ Prototype class for the genration of tests cases for the fields
        of every Resource

        """

        @staticmethod
        def generate_field_test_data(field):
            field_classname = field.__class__.__name__
            if field_classname == 'CharField':
                bad_value = "abcd"
            elif field_classname == "IntegerField":
                bad_value = 12345
            elif field_classname == "ToManyField":
                (uri, res) = field.to_class().create_test_resource()
                return [uri]
            elif field_classname == "ToOneField" or field_classname == "ForeignKey":
                (uri, res) = field.to_class().create_test_resource()
                return [uri]
            elif field_classname == "DateField":
                return datetime.now()
            elif field_classname == "DictField":
                return {}
            else:
                raise FieldNotSupportedException(field_classname)

            return bad_value

        @staticmethod
        def multi_post_missing_fields_nice_response(
                self, resource_name, resource, field_name, field):
            """ For each field in the resource, removes it from the resource
            and post a request with the missing field, then it verifies that
            no ugly response is given, like a 500 status code, or a non-json
            response

            """
            if resource.can_create():
                post_data = prepare_test_post_data(self, resource)
                try:
                    del post_data[field_name]
                except:
                    return

                response = self.client.post(resource.get_resource_list_uri(),
                    post_data)

                for code in [401, 404, 500]:
                    msg = "%s returns a %s response when issuing a POST with" \
                            " missing %s - %s"
                    msg %= (resource_name, code, field_name, response.content)
                    self.assertNotEqual(code, response.status_code, msg)
                header, content_type = response._headers['content-type']

                if len(response.content) > 0:
                    msg = "Bad content type when POSTing a %s with missing %s:" \
                          "%s (%s)=> %s"
                    msg %= (resource_name, field_name, content_type,
                            response.status_code, response.content)
                    self.assertTrue(
                            content_type.startswith('application/json'), msg)

        @staticmethod
        def multi_help(self, resource_name, resource, field_name, field):
            """ Verifies that every field has a help_text set """
            if field_name == 'id':
                return
            if field.help_text == field.__class__.help_text:
                msg = "Missing help text for %s.%s resource field."
                msg %= (resource_name, field_name)
                self.assertTrue(False, msg)

        @staticmethod
        def multi_readonly_post(self, resource_name, resource, field_name,
            field):
            """ for every read only field, tries to change it's value through
            POST and verifies it didn't

            """
            if field.readonly and resource.can_create():
                post_data = resource.get_test_post_data()
                try:
                    bad_value = UnderResourceFields.generate_field_test_data(field)
                except FieldNotSupportedException:
                    return
                post_data[field_name] = bad_value
                post_response = self.client.post(
                        resource.get_resource_list_uri(),
                        post_data, parse='json')

                if post_response.status_code == 201:
                    location = post_response['Location']
                    get_response = self.client.get(location, parse='json')
                    msg = "Could not read posted resource (%d)\n%s"
                    msg %= (get_response.status_code, get_response.content)
                    self.assertEqual(get_response.status_code, 200, msg)

                    msg = "%s.%s can be set by a POST request even though"\
                        " it's readonly!."
                    msg %= (resource_name, field_name)
                    self.assertNotEqual(get_response.get(field_name, ''),
                       bad_value, msg)

        @staticmethod
        def multi_max_length_post(self, resource_name, resource, field_name,
                field):

            max_length = getattr(field, "max_length", None)
            if max_length is not None and resource.can_create():
                request_data = resource.get_test_post_data()

                request_data[field_name] = \
                UnderResourceFields.generate_string_by_length(
                        field.max_length + 1)
                msg = "%s.%s max length exceeded, and did not return"\
                        " a bad request error"
                msg %= (resource_name, field_name)
                post_response = self.client.post(
                        resource.get_resource_list_uri(),
                        data=request_data, parse='json')

                self.assertEqual(post_response.status_code, 400, msg)
                data = post_response.data['errors']
                has_error = False
                for error in data:
                    if error['name'] == "MaxLengthExceeded":
                        has_error = True
                if has_error is False:
                    msg = '%s.%s max length exceeded, but MaxLengthExceeded error is not being reported'
                    msg %= (resource_name, field_name)
                    self.assertTrue(False, msg)

        @staticmethod
        def multi_readonly_patch(self, resource_name, resource, field_name,
            field):
            """ for every read only field, tries to change it's value through
            PATCH and verifies it didn't

            """

            client = Client()

            if field.readonly and resource.can_patch():
                #Create a resource to modify it
                (location, obj) = resource.create_test_resource()
                bad_value = UnderResourceFields.generate_field_test_data(field)

                #attempt to PATCH
                patch_data = {}
                patch_data[field_name] = bad_value
                self.client.patch(location, patch_data, parse='json')
                get_response = client.get(location, parse='json')

                msg = "%s.%s can be changed by a PATCH and it's readonly!\n%s"
                msg %= (resource_name, field_name, get_response)

                self.assertTrue(get_response.data is not None,
                        "No response data from %s \nWith data: %s" %
                        (location, patch_data))

                self.assertNotEqual(get_response.data.get(field_name, None),
                    bad_value, msg)

        @staticmethod
        def generate_arguments():
            args = []
            for resource_name, resource in api._registry.items():
                if hasattr(resource._meta, "testdata"):
                    for field_name, field in resource.fields.items():
                        args.append((resource_name, resource, field_name,
                            field))

            return args

        @staticmethod
        def generate_test_name(resource_name, resource, field_name, field):
            return "_".join([resource_name, field_name])

        @staticmethod
        def generate_string_by_length(length):

            string = ""
            for i in range(length):
                rand_num = random.randint(0, 35)
                if rand_num < 10:
                    char = str(rand_num)
                else:
                    char = chr(55 + rand_num)
                string += char
            return string

        @staticmethod
        def setUp(self, *args, **kwargs):
            self.client = Client()
            user_setUp(self, *args, **kwargs)

    class TestResourceFields(TestCase):
        __metaclass__ = create_multi_meta(UnderResourceFields)

    return TestResourceFields
