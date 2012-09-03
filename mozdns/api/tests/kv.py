from django.test import TestCase
from django.test.client import Client, FakePayload, MULTIPART_CONTENT, encode_multipart, BOUNDARY
from django.utils.encoding import smart_str

from tastypie.test import ResourceTestCase

from core.interface.static_intr.models import StaticInterface
from core.interface.static_intr.models import StaticIntrKeyValue
from mozdns.utils import ensure_label_domain, prune_tree
from mozdns.tests.view_tests_template import GenericViewTests, random_label
from mozdns.tests.view_tests_template import random_byte
from mozdns.cname.models import CNAME
from mozdns.address_record.models import AddressRecord
from mozdns.domain.models import Domain
from mozdns.mx.models import MX
from mozdns.ptr.models import PTR
from mozdns.nameserver.models import Nameserver
from mozdns.soa.models import SOA
from mozdns.srv.models import SRV
from mozdns.txt.models import TXT
from mozdns.sshfp.models import SSHFP
from mozdns.view.models import View

import simplejson as json
from urlparse import urlparse, urlsplit
import pdb

API_VERSION = '1'

class KVAPITests(object):
    object_list_url = "/mozdns/api/v{0}_dns/{1}/"
    object_url = "/mozdns/api/v{0}_dns/{1}/{2}/"

    def setUp(self):
        super(KVAPITests, self).setUp()

    def test_create(self):
        pdb.set_trace()
        resp, post_data = self.generic_create(self.post_data())
        _, _, (_, new_object_url) = resp.items()
        new_resp = self.api_client.get(new_object_url, format='json')
        self.assertValidJSONResponse(new_resp)
        new_obj_data = json.loads(new_resp.content)
        for key in post_data.keys():
            self.assertEqual(post_data[key], new_obj_data[key])

    def test_update(self):
        # Are these test's failing? See this bug.
        # https://github.com/toastdriven/django-tastypie/issues/597
        # Please monkey patch tastypie
        # tastypie/test.py Line
        # diff --git a/tastypie/test.py b/tastypie/test.py
        # index e395158..27f813f 100644
        # --- a/tastypie/test.py
        # +++ b/tastypie/test.py
        # @@ -161,6 +161,8 @@ class TestApiClient(object):
        #
        #          if data is not None:
        #              kwargs['data'] = self.serializer.serialize(data, format=content_type)
        # +            if content_type == 'application/json':
        # +                kwargs['data'] = str(kwargs['data'])
        #
        #  if authentication is not None:
        #     kwargs['HTTP_AUTHORIZATION'] = authentication

        resp, post_data = self.generic_create(self.post_data())
        _, _, (_, new_object_url) = resp.items()
        update_resp, patch_data = self.generic_update(new_object_url,
                self.post_data())

        # Now make sure the data used to patch is sticking to the model.
        patch_resp = self.api_client.get(new_object_url, format='json')
        self.assertValidJSONResponse(patch_resp)
        patch_obj_data = json.loads(patch_resp.content)
        for key in patch_data.keys():
            self.assertEqual(patch_data[key], patch_obj_data[key])

    def test_delete(self):
        obj_count = self.test_type.objects.count()
        resp, post_data = self.generic_create(self.post_data())
        _, _, (_, new_object_url) = resp.items()
        self.assertEqual(self.test_type.objects.count(), obj_count+1)
        resp = self.api_client.delete(new_object_url, format='json')
        self.assertHttpAccepted(resp)
        self.assertEqual(self.test_type.objects.count(), obj_count)

    def generic_update(self, patch_url, patch_data):
        obj_count = self.test_type.objects.count()
        resp = self.api_client.patch(patch_url, format='json',
                    data=patch_data)
        self.assertHttpAccepted(resp)
        # Verify a no new object has been added.
        self.assertEqual(self.test_type.objects.count(), obj_count)
        return resp, patch_data


    def generic_create(self, post_data):
        # Check how many are there first.
        obj_count = self.test_type.objects.count()
        create_url = self.object_list_url.format(API_VERSION,
                        str(self.test_type.__name__).lower())
        resp = self.api_client.post(create_url, format='json', data=post_data)
        self.assertHttpCreated(resp)
        # Verify a new one has been added.
        self.assertEqual(self.test_type.objects.count(), obj_count + 1)
        return resp, post_data

    def test_bad_value_create(self):
        post_data = self.bad_post_data()
        obj_count = self.test_type.objects.count()
        create_url = self.object_list_url.format(API_VERSION,
                        str(self.test_type.__name__).lower())
        resp = self.api_client.post(create_url, format='json', data=post_data)
        self.assertHttpBadRequest(resp)
        self.assertEqual(self.test_type.objects.count(), obj_count)

    def test_bad_value_update(self):
        good_post_data = self.good_post_data()
        resp, post_data = self.generic_create(good_post_data)
        self.assertHTTPCreated(resp)
        _, _, (_, new_object_url) = resp.items()

        resp = self.api_client.patch(new_object_url, format='json',
                data=self.bad_post_data())
        self.assertHttpBadRequest(resp)

        new_resp = self.api_client.get(new_object_url, format='json')
        self.assertValidJSONResponse(new_resp)
        new_obj_data = json.loads(new_resp.content)
        self.assertEqual(good_post_data, new_obj_data)


class StaticIntrKVAPITests(KVAPITests, ResourceTestCase):
    test_type = StaticIntrKeyValue

    def post_data(self):
        return {
            'key': random_label(),
            'value': random_label(),
        }

    def bad_post_data(self):
        """Let's see what happens when we cause a ValidationError
        """
        return {
            'key': 'interface_type',
            'value': 'asdf'
        }

    def good_post_data(self):
        return {
            'key': 'interface_type',
            'value': 'eth'
        }
