from django.test import TestCase
from django.test.client import Client, FakePayload, MULTIPART_CONTENT, encode_multipart, BOUNDARY
from django.utils.encoding import smart_str

from tastypie.test import ResourceTestCase

from mozdns.tests.view_tests_template import GenericViewTests, random_label
from mozdns.tests.view_tests_template import random_byte
from mozdns.cname.models import CNAME
from mozdns.address_record.models import AddressRecord
from mozdns.domain.models import Domain
from mozdns.mx.models import MX
from mozdns.soa.models import SOA
from mozdns.srv.models import SRV
from mozdns.txt.models import TXT
from mozdns.sshfp.models import SSHFP

import simplejson as json
from urlparse import urlparse, urlsplit
import pdb

API_VERSION = '1'

def build_sample_domain():
    domain_name = ''
    for i in range(2):
        domain_name = random_label()
        domain = Domain(name=domain_name)
    soa = SOA(primary=random_label(), contact="asf", comment=random_label())
    soa.save()
    domain.soa = soa
    domain.save()
    return domain

class MozdnsAPITests(object):
    object_list_url = "/mozdns/api/v{0}_dns/{1}/"
    object_url = "/mozdns/api/v{0}_dns/{1}/{2}/"

    def setUp(self):
        super(MozdnsAPITests, self).setUp()
        self.domain = build_sample_domain()

    def test_create(self):
        resp, post_data = self.generic_create()
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

        resp, post_data = self.generic_create()
        _, _, (_, new_object_url) = resp.items()
        update_resp, patch_data = self.generic_update(new_object_url)

        # Now make sure the data used to patch is sticking to the model.
        patch_resp = self.api_client.get(new_object_url, format='json')
        self.assertValidJSONResponse(patch_resp)
        patch_obj_data = json.loads(patch_resp.content)
        for key in patch_data.keys():
            self.assertEqual(patch_data[key], patch_obj_data[key])

    def test_delete(self):
        obj_count = self.test_type.objects.count()
        resp, post_data = self.generic_create()
        _, _, (_, new_object_url) = resp.items()
        self.assertEqual(self.test_type.objects.count(), obj_count+1)
        resp = self.api_client.delete(new_object_url, format='json')
        self.assertHttpAccepted(resp)
        self.assertEqual(self.test_type.objects.count(), obj_count)

    def generic_update(self, patch_url):
        obj_count = self.test_type.objects.count()
        patch_data = self.post_data()
        resp = self.api_client.patch(patch_url, format='json',
                    data=patch_data)
        self.assertHttpAccepted(resp)
        # Verify a no new object has been added.
        self.assertEqual(self.test_type.objects.count(), obj_count)
        return resp, patch_data

    def generic_create(self):
        # Check how many are there first.
        obj_count = self.test_type.objects.count()
        create_url = self.object_list_url.format(API_VERSION,
                str(self.test_type.__name__).lower())
        post_data = self.post_data()
        resp = self.api_client.post(create_url, format='json', data=post_data)
        self.assertHttpCreated(resp)
        # Verify a new one has been added.
        self.assertEqual(self.test_type.objects.count(), obj_count + 1)
        return resp, post_data



class CNAMEAPITests(MozdnsAPITests, ResourceTestCase):
    test_type = CNAME

    def post_data(self):
        return {
            'label': random_label(),
            'domain':self.domain.name,
            'target':random_label()
        }


class MXAPITests(MozdnsAPITests, ResourceTestCase):
    test_type = MX

    def post_data(self):
        return {
            'label': random_label(),
            'domain':self.domain.name,
            'server':random_label(),
            'priority':123,
            'ttl':213
        }

class SRVAPITests(MozdnsAPITests, ResourceTestCase):
    test_type = SRV
    def post_data(self):
        return {
            'label':"_"+random_label(),
            'domain':self.domain.name,
            'target':random_label(),
            'priority':2 ,
            'weight':2222 ,
            'port': 222
        }


class TXTAPITests(MozdnsAPITests, ResourceTestCase):
    test_type = TXT
    def post_data(self):
        return {
            'label':random_label(),
            'domain':self.domain.name,
            'txt_data':random_label()
        }


class SSHFPAPITests(MozdnsAPITests, ResourceTestCase):
    test_type = SSHFP
    def post_data(self):
        return {
            'label':random_label(),
            'domain': self.domain.name,
            'algorithm_number': 1,
            'fingerprint_type': 1,
            'key':random_label()
        }

class AdderessRecordV4APITests(MozdnsAPITests, ResourceTestCase):
    test_type = AddressRecord
    def setUp(self):
        Domain.objects.get_or_create(name='arap')
        Domain.objects.get_or_create(name='in-addr.arap')
        Domain.objects.get_or_create(name='10.in-addr.arap')
        super(AdderessRecordV4APITests, self).setUp()

    def post_data(self):
        return {
            'label':random_label(),
            'domain': self.domain.name,
            'ip_str': "10.{0}.{1}.{2}".format(random_byte(), random_byte(), random_byte()),
            'ip_type': '4'
        }

class AdderessRecordV6APITests(MozdnsAPITests, ResourceTestCase):
    test_type = AddressRecord
    def setUp(self):
        Domain.objects.get_or_create(name='arap')
        Domain.objects.get_or_create(name='ipv6.arap')
        Domain.objects.get_or_create(name='1.ipv6.arap')
        super(AdderessRecordV6APITests, self).setUp()

    def post_data(self):
        return {
            'label':random_label(),
            'domain': self.domain.name,
            'ip_str': "1000:{0}:{1}:{2}::".format(random_byte(), random_byte(),
                random_byte()),
            'ip_type': '6'
        }
