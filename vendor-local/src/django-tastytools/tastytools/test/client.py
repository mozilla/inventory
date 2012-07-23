from django.test import Client as DjangoClient
from django.core.serializers import json
from django.test.client import MULTIPART_CONTENT, BOUNDARY
from django.test.client import encode_multipart, FakePayload
from django.utils.http import urlencode
from django.utils import simplejson
from urlparse import urlparse
from tastypie.resources import Resource
from datetime import datetime

def extended_response(method):
    def wrapped(*args, **kwargs):
        start = datetime.now()
        response = method(*args, **kwargs)
        response.crono_end = datetime.now()
        response.crono_start = start
        return response
    return wrapped

class Client(DjangoClient):
    '''Extends the django client to add patch method support and
    makes it easier to send/receive json data'''

    def __init__(self, *args, **kwargs):
        super(Client, self).__init__(*args, **kwargs)

    def login(self, user=None, **kwargs):
        if len(kwargs) == 0 and user is not None:
            return super(Client, self).login(username=user.username,
                password=user.username)
        else:
            return super(Client, self).login(**kwargs)

    def _path_or_resource(self, path, obj=None):
        '''If passed a Resource object, will return its URI.
           If passed a path, will return the path unmodified'''

        if isinstance(path, Resource):
           if obj is not None:
               return path.get_resource_uri(obj)
           else:
                return path.get_resource_list_uri()
        else:
           return path

    def patch_request(self, path, data=False,
        content_type=MULTIPART_CONTENT, **extra):
        "Construct a PATCH request."

        data = data or {}

        if content_type is MULTIPART_CONTENT:
            post_data = encode_multipart(BOUNDARY, data)
        else:
            post_data = data

        # Make `data` into a querystring only if it's not already a string. If
        # it is a string, we'll assume that the caller has already encoded it.
        query_string = None
        if not isinstance(data, basestring):
            query_string = urlencode(data, doseq=True)

        parsed = urlparse(path)
        request_params = {
            'CONTENT_LENGTH': len(post_data),
            'CONTENT_TYPE':   content_type,
            'PATH_INFO':      self._get_path(parsed),
            'QUERY_STRING':   query_string or parsed[4],
            'REQUEST_METHOD': 'PATCH',
            'wsgi.input':     FakePayload(post_data),
        }
        request_params.update(extra)
        return self.request(**request_params)

    @extended_response
    def patch(self, path, data=None, follow=False,
        content_type="application/json", parse="json", **extra):
        """
        Send a resource patch to the server using PATCH.
        """

        data = data or {}
        path = self._path_or_resource(path, data)

        if type(data) == dict and content_type == "application/json":
            data = simplejson.dumps(data, cls=json.DjangoJSONEncoder)

        response = self.patch_request(path, data=data,
            content_type=content_type, **extra)

        if parse == "json":
            try:
                response.data = simplejson.loads(response.content)
            except:
                response.data = None


        if follow:
            response = self._handle_redirects(response, **extra)
        return response

    @extended_response
    def post(self, path, data=None, content_type='application/json',
        follow=False, parse='json', **extra):
        """
        Overloads default Django client POST request to setdefault content
        type to applcation/json and automatically sets data to a raw json
        string.
        """

        path = self._path_or_resource(path)
        data = data or {}

        if type(data) == dict and content_type == "application/json":
            data = simplejson.dumps(data, cls=json.DjangoJSONEncoder)

        response = super(Client, self).post(path, data, content_type,
            follow=False, **extra)

        if parse == "json":
            try:
                response.data = simplejson.loads(response.content)
            except:
                response.data = None
        return response

    @extended_response
    def put(self, path, data=None, content_type='application/json',
        follow=False, parse='json', **extra):
        """
        Overloads default Django client PUT request to setdefault content type
        to applcation/json and automatically sets data to a raw json string.
        """

        path = self._path_or_resource(path, data)
        data = data or {}

        if type(data) == dict:
            data = simplejson.dumps(data, cls=json.DjangoJSONEncoder)

        response = super(Client, self).put(path, data, content_type, **extra)

        if parse == "json":
            try:
                response.data = simplejson.loads(response.content)
            except:
                response.data = None
        return response

    @extended_response
    def delete(self, path, follow=False, obj=None, **extra):
        """
        Overloads default Django client DELETE request to setdefault content type
        to applcation/json and automatically sets data to a raw json string.
        """

        path = self._path_or_resource(path, obj)
        return super(Client, self).delete(path, **extra)

    @extended_response
    def get(self, path, data=None, follow=False, parse='json', obj=None, **extra):
        """
        Overloads default Django client GET request to receive a parse
        parameter. When parse='json', the server's response is parsed using
        simplejson and loaded into request.data.
        """

        path = self._path_or_resource(path, obj)
        data = data or {}
        response = super(Client, self).get(path, data, follow, **extra)

        if parse == "json":
            try:
                response.data = simplejson.loads(response.content)
            except Exception:
                response.data = None
        return response

    def rpc(self, method, **kwargs):
        """
        Issues a POST request using the JSONRPC 2.0 specification.
        """

        post_data = {
            "jsonrpc": "2.0",
            "method": method,
            "params": kwargs,
            "id": 1,
        }

        return self.post("/api/rpc/", post_data, parse='json')


class MultiTestCase(object):

    def setUp(self):
        print "setup"
        pass

    @staticmethod
    def generate_arguments():
        '''Must return a list of tuples which will be used to call each
        generated test'''

        raise Exception("Not implemented!")

    @staticmethod
    def generate_test_name():
        '''Given a tuple generated by the generate_arguments() method, it
        must return a name for the generated test.'''

        raise Exception("Not implemented!")


def create_multi_meta(multi_class):
    '''Creates the meta class for a test case generator, the supplied
    generator class must implement the generate_arguments() and
    generate_test_name() methods, all other class methods that generate tests
    must be called "multi_*"

    '''
    class MetaTest(type):

        def __new__(mcs, name, bases, attrs):
            funcs = [test for test in dir(multi_class)
                if test.startswith("multi_")]

            def doTest(test, *args):
                '''Generates the actual test function.'''

                def test_func(self):
                    '''The genereated test function.'''

                    multitest = multi_class()
                    multitest.setUp(self, getattr(multitest, test), *args)
                    getattr(multitest, test)(self, *args)

                return test_func

            for func in funcs:
                for args in multi_class.generate_arguments():
                    test_func_name = 'test_gen_%s_%s'
                    test_func_name %= (func,
                        multi_class.generate_test_name(*args))

                    attrs[test_func_name] = doTest(func, *args)
            return type.__new__(mcs, name, bases, attrs)

    return MetaTest
