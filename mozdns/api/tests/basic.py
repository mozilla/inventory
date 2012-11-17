from django.test import TestCase
from django.test.client import Client, FakePayload, MULTIPART_CONTENT, encode_multipart, BOUNDARY
from django.utils.encoding import smart_str

from tastypie.test import ResourceTestCase

from systems.models import System
from core.interface.static_intr.models import StaticInterface
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

def build_sample_domain():
    domain_name = ''
    for i in range(2):
        domain_name = random_label()
        domain = Domain(name=domain_name)
    soa = SOA(primary=random_label(), contact="asf", description=random_label())
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
        View(name='public').save()
        View(name='private').save()

    def test_create(self):
        resp, post_data = self.generic_create(self.post_data())
        _, (_, new_object_url) = resp.items()
        new_resp = self.api_client.get(new_object_url, format='json')
        self.assertValidJSONResponse(new_resp)
        new_obj_data = json.loads(new_resp.content)
        self.compare_data(post_data, new_obj_data)

    def compare_data(self, old_data, new_obj_data):
        for key in old_data.keys():
            self.assertEqual(old_data[key], new_obj_data[key])

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

        post_data = self.post_data()
        resp, post_data = self.generic_create(post_data)
        _, (_, new_object_url) = resp.items()
        patch_data = self.post_data()
        update_resp, patch_data = self.generic_update(new_object_url,
                patch_data)

        # Now make sure the data used to patch is sticking to the model.
        patch_resp = self.api_client.get(new_object_url, format='json')
        self.assertValidJSONResponse(patch_resp)
        patch_obj_data = json.loads(patch_resp.content)
        self.compare_data(patch_data, patch_obj_data)

    def test_delete(self):
        obj_count = self.test_type.objects.count()
        resp, post_data = self.generic_create(self.post_data())
        _, (_, new_object_url) = resp.items()
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

    def test_changing_only_one_field(self):
        resp, post_data = self.generic_create(self.post_data())
        _, (_, new_object_url) = resp.items()
        change_post_data = {}
        change_post_data['description'] = "==DIFFERENT=="
        post_data['description'] = "==DIFFERENT=="
        resp, patch_data = self.generic_update(new_object_url, change_post_data)
        new_resp = self.api_client.get(new_object_url, format='json')
        updated_obj_data = json.loads(new_resp.content)
        self.compare_data(post_data, updated_obj_data)

    def test_views(self):
        post_data = self.post_data()
        post_data['views'] = ['public']
        obj_count = self.test_type.objects.count()
        create_url = self.object_list_url.format(API_VERSION,
                        str(self.test_type.__name__).lower())
        resp = self.api_client.post(create_url, format='json', data=post_data)
        self.assertHttpCreated(resp)
        self.assertEqual(self.test_type.objects.count(), obj_count + 1)
        # Get the object and check it's views
        _, (_, new_object_url) = resp.items()
        new_resp = self.api_client.get(new_object_url, format='json')
        self.assertValidJSONResponse(new_resp)
        new_obj_data = json.loads(new_resp.content)
        self.assertTrue('views' in new_obj_data)
        self.assertEqual(new_obj_data['views'], ['public'])
        # Update to both views
        views = ['public', 'private']
        post_data = {'views': views}
        obj_count = self.test_type.objects.count()
        resp, patch_data = self.generic_update(new_object_url, post_data)
        self.assertEqual(self.test_type.objects.count(), obj_count)
        self.assertTrue('views' in new_obj_data)
        new_resp = self.api_client.get(new_object_url, format='json')
        updated_obj_data = json.loads(new_resp.content)
        for view_name in updated_obj_data['views']:
            self.assertTrue(view_name in views)

        # Now try deleteing a view.
        views = ['private']
        post_data = {'views': ['no-public']}  # This should delete public
        obj_count = self.test_type.objects.count()
        resp, patch_data = self.generic_update(new_object_url, post_data)
        self.assertEqual(self.test_type.objects.count(), obj_count)
        self.assertTrue('views' in new_obj_data)
        new_resp = self.api_client.get(new_object_url, format='json')
        updated_obj_data = json.loads(new_resp.content)
        for view_name in updated_obj_data['views']:
            self.assertTrue(view_name in views)


class MangleTests(ResourceTestCase):
    test_type = CNAME
    object_list_url = "/mozdns/api/v{0}_dns/{1}/"
    object_url = "/mozdns/api/v{0}_dns/{1}/{2}/"

    def setUp(self):
        super(MangleTests, self).setUp()
        self.domain = build_sample_domain()
        View(name='public').save()
        View(name='private').save()

    def test_missing_key(self):
        post_data = self.post_data()
        post_data.pop('fqdn')
        obj_count = self.test_type.objects.count()
        create_url = self.object_list_url.format(API_VERSION,
                        str(self.test_type.__name__).lower())
        resp = self.api_client.post(create_url, format='json', data=post_data)
        self.assertHttpBadRequest(resp)
        self.assertEqual(self.test_type.objects.count(), obj_count)

    def test_mangled_key(self):
        post_data = self.post_data()
        post_data['fqdn'] = post_data['fqdn'] + '.'
        obj_count = self.test_type.objects.count()
        create_url = self.object_list_url.format(API_VERSION,
                        str(self.test_type.__name__).lower())
        resp = self.api_client.post(create_url, format='json', data=post_data)
        self.assertHttpBadRequest(resp)
        self.assertEqual(self.test_type.objects.count(), obj_count)

    def test_bad_fqdn(self):
        post_data = self.post_data()
        post_data['fqdn'] = ''
        obj_count = self.test_type.objects.count()
        create_url = self.object_list_url.format(API_VERSION,
                        str(self.test_type.__name__).lower())
        resp = self.api_client.post(create_url, format='json', data=post_data)
        self.assertHttpBadRequest(resp)
        self.assertEqual(self.test_type.objects.count(), obj_count)


    def test_ensure_label_domain_fail(self):
        # MAke ensure_label_domain fail
        post_data = self.post_data()
        Domain.objects.get_or_create(name="asdf")
        Domain.objects.get_or_create(name="foo.asdf")
        domain , _= Domain.objects.get_or_create(name="bar.foo.asdf")
        post_data['fqdn'] = 'secondbar.x.y.' + domain.name
        obj_count = self.test_type.objects.count()
        create_url = self.object_list_url.format(API_VERSION,
                        str(self.test_type.__name__).lower())
        resp = self.api_client.post(create_url, format='json', data=post_data)
        self.assertHttpBadRequest(resp)
        self.assertEqual(self.test_type.objects.count(), obj_count)

    def post_data(self):
        return {
            'description':random_label(),
            'ttl': random_byte(),
            'fqdn': 'b' + random_label() + "." + self.domain.name,
            'target':random_label()
        }

class DomainLeakTests(ResourceTestCase):
    test_type = CNAME
    object_list_url = "/mozdns/api/v{0}_dns/{1}/"
    object_url = "/mozdns/api/v{0}_dns/{1}/{2}/"

    def setUp(self):
        super(DomainLeakTests, self).setUp()
        self.domain = build_sample_domain()

    def test_leak1(self):
        # Check how many are there first.
        domain_count = Domain.objects.count()
        create_url = self.object_list_url.format(API_VERSION,
                str(self.test_type.__name__).lower())
        post_data = self.post_data()
        resp = self.api_client.post(create_url, format='json', data=post_data)
        self.assertHttpBadRequest(resp)
        # Verify a new one has been added.
        self.assertEqual(Domain.objects.count(), domain_count)
        self.assertTrue(Domain.objects.get(pk=self.domain.pk))  # paranoia
        return resp, post_data

    def post_data(self):
        return {
            # We are fucking this up on purpose.
            'fuckinup': random_label(),
            'fqdn': 'c' + random_label() + '.' + random_label() + '.' + self.domain.name,
        }

class CNAMEAPITests(MozdnsAPITests, ResourceTestCase):
    test_type = CNAME

    def post_data(self):
        return {
            'description':random_label(),
            'ttl': random_byte(),
            'fqdn': 'd' + random_label() + "." + self.domain.name,
            'target': random_label()
        }


class MXAPITests(MozdnsAPITests, ResourceTestCase):
    test_type = MX

    def post_data(self):
        return {
            'description': random_label(),
            'ttl': random_byte(),
            'fqdn':  'e' + random_label() + "." + self.domain.name,
            'server': random_label(),
            'priority':123,
            'ttl':213
        }

class SRVAPITests(MozdnsAPITests, ResourceTestCase):
    test_type = SRV
    def post_data(self):
        return {
            'description': random_label(),
            'ttl': random_byte(),
            'fqdn':"_"+random_label() + "." + self.domain.name,
            'target': random_label(),
            'priority':2 ,
            'weight':2222 ,
            'port': 222
        }


class TXTAPITests(MozdnsAPITests, ResourceTestCase):
    test_type = TXT
    def post_data(self):
        return {
            'description': random_label(),
            'ttl': random_byte(),
            'fqdn': 'f' + random_label() + "." + self.domain.name,
            'txt_data': random_label()
        }

class NameserverAPITests(MozdnsAPITests, ResourceTestCase):
    test_type = Nameserver
    def test_fqdn_create(self):
        pass
    def post_data(self):
        return {
            'server': 'g' + random_label(),
            'description': random_label(),
            'ttl': random_byte(),
            'domain':self.domain.name,
        }


class SSHFPAPITests(MozdnsAPITests, ResourceTestCase):
    test_type = SSHFP
    def post_data(self):
        return {
            'description': random_label(),
            'ttl': random_byte(),
            'fqdn': 'h' + random_label() + "." + self.domain.name,
            'algorithm_number': 1,
            'fingerprint_type': 1,
            'key': random_label()
        }

class AdderessRecordV4APITests(MozdnsAPITests, ResourceTestCase):
    test_type = AddressRecord
    def setUp(self):
        super(AdderessRecordV4APITests, self).setUp()

    def post_data(self):
        return {
            'description': random_label(),
            'ttl': random_byte(),
            'fqdn': 'i' + random_label() + "." + self.domain.name,
            'ip_str': "11.{0}.{1}.{2}".format(random_byte(), random_byte(), random_byte()),
            'ip_type': '4'
        }

class AdderessRecordV6APITests(MozdnsAPITests, ResourceTestCase):
    test_type = AddressRecord
    def setUp(self):
        #Domain.objects.get_or_create(name='arap')
        #Domain.objects.get_or_create(name='ipv6.arap')
        #Domain.objects.get_or_create(name='1.ipv6.arap')
        super(AdderessRecordV6APITests, self).setUp()

    def post_data(self):
        return {
            'description': random_label(),
            'ttl': random_byte(),
            'fqdn': 'j' + random_label() + "." + self.domain.name,
            'ip_str': "1000:{0}:{1}:{2}::".format(random_byte(), random_byte(),
                random_byte()),
            'ip_type': '6'
        }

class PTRV6APITests(MozdnsAPITests, ResourceTestCase):
    test_type = PTR
    def setUp(self):
        Domain.objects.get_or_create(name='arpa')
        Domain.objects.get_or_create(name='ip6.arpa')
        Domain.objects.get_or_create(name='1.ip6.arpa')
        super(PTRV6APITests, self).setUp()

    def test_fqdn_create(self):
        pass

    def post_data(self):
        return {
            'description': 'k' + random_label(),
            'ttl': random_byte(),
            'ip_str': "1000:{0}:{1}:{2}:{3}:{4}::".format(random_byte(), random_byte(),
                random_byte(),random_byte(),random_byte()),
            'ip_type': '6',
            'name': random_label()
        }

class PTRV4APITests(MozdnsAPITests, ResourceTestCase):
    test_type = PTR
    def setUp(self):
        Domain.objects.get_or_create(name='arpa')
        Domain.objects.get_or_create(name='in-addr.arpa')
        Domain.objects.get_or_create(name='11.in-addr.arpa')
        super(PTRV4APITests, self).setUp()

    def test_fqdn_create(self):
        pass

    def post_data(self):
        return {
            'description': random_label(),
            'ttl': random_byte(),
            'ip_str': "11.{0}.{1}.{2}".format(random_byte(), random_byte(), random_byte()),
            'ip_type': '4',
            'name': random_label()
        }

class StaticIntrV4APITests(MozdnsAPITests, ResourceTestCase):
    test_type = StaticInterface
    def setUp(self):
        Domain.objects.get_or_create(name='arpa')
        Domain.objects.get_or_create(name='in-addr.arpa')
        Domain.objects.get_or_create(name='11.in-addr.arpa')
        super(StaticIntrV4APITests, self).setUp()
        self.s = System(hostname="foobar")
        self.s.save()

    def compare_data(self, old_data, new_obj_data):
        for key in old_data.keys():
            if key == 'system_hostname':
                self.assertEqual(old_data[key], new_obj_data['system']['hostname'])
                continue
            if key in ('iname', 'system') :
                continue  # StaticInterface needs this done. Too lazy to factor
                          # a comparison function out
            self.assertEqual(old_data[key], new_obj_data[key])

    def test_create_hostname(self):
        post_data = self.post_data()
        del post_data['system']
        post_data['system_hostname'] = self.s.hostname
        resp, post_data = self.generic_create(post_data)
        _, (_, new_object_url) = resp.items()
        new_resp = self.api_client.get(new_object_url, format='json')
        self.assertValidJSONResponse(new_resp)
        new_obj_data = json.loads(new_resp.content)
        self.compare_data(post_data, new_obj_data)

    def post_data(self):
        return {
            'description': 'm' + random_label(),
            'ttl': random_byte(),
            'mac': '11:22:33:44:55:00',
            'system': '/tasty/v3/system/{0}/'.format(self.s.pk),
            'fqdn': 'a' + random_label() + "." + self.domain.name,
            'iname': 'eth2.4',
            'dhcp_enabled': False,
            'dns_enabled': True,
            'ip_str': "11.255.{0}.{1}".format(random_byte(), random_byte()),
            'ip_type': '4'
        }

class StaticIntrV6APITests(MozdnsAPITests, ResourceTestCase):
    test_type = StaticInterface
    def setUp(self):
        Domain.objects.get_or_create(name='arpa')
        Domain.objects.get_or_create(name='ip6.arpa')
        Domain.objects.get_or_create(name='2.ip6.arpa')
        super(StaticIntrV6APITests, self).setUp()
        self.s = System(hostname="foobar")
        self.s.save()

    def compare_data(self, old_data, new_obj_data):
        for key in old_data.keys():
            if key == 'iname' or key == 'system':
                continue  # StaticInterface needs this done. Too lazy to factor
                          # a comparison function out
            self.assertEqual(old_data[key], new_obj_data[key])

    def post_data(self):
        return {
            'description': random_label(),
            'ttl': random_byte(),
            'fqdn': 'p' + random_label() + "." + self.domain.name,
            'iname': 'mgmt4',
            'dhcp_enabled': True,
            'dns_enabled': True,
            'mac': '11:22:33:44:55:00',
            'system': '/tasty/v3/system/{0}/'.format(self.s.pk),
            'ip_str': "2000:a{0}:a{1}:a{2}::".format(random_byte(), random_byte(),
                random_byte()),
            'ip_type': '6'
        }
