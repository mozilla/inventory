from django.test import TestCase
from django.test.client import Client
from django.http import Http404

from mozdns.tests.view_tests import random_label
from mozdns.tests.view_tests import random_byte
from mozdns.domain.models import Domain
from mozdns.address_record.models import AddressRecord
from mozdns.ptr.models import PTR
from mozdns.txt.models import TXT
from mozdns.cname.models import CNAME
from mozdns.mx.models import MX
from mozdns.srv.models import SRV
from mozdns.nameserver.models import Nameserver
from mozdns.master_form.views import commit_record
from mozdns.view.models import View

import simplejson as json
import pdb


class MasterFormTests(TestCase):
    def setUp(self):
        self.c = Client()
        self.d, _ = Domain.objects.get_or_create(name="com")
        Domain.objects.get_or_create(name="arpa")
        Domain.objects.get_or_create(name="in-addr.arpa")
        Domain.objects.get_or_create(name="10.in-addr.arpa")

    def craft_ip_str(self):
        data = {
            'ip_str': "10.{0}.{1}.{2}".format(random_byte(), random_byte(),
                random_byte(), random_byte())
        }
        return data

    def craft_label_domain(self):
        data = {
                'label': random_label(),
                'domain': self.d.name
                }
        return data

    def craft_number_dict(self, field):
        data = {field: random_byte()}
        return data

    def craft_name_dict(self, field):
        data = {field: random_label() + "." + random_label()}
        return data

    def craft_ttl_and_comment(self):
        data = {
                'ttl': random_byte(),
                'comment': random_label()
                }
        return data

    def test_A(self):
        data = {'rtype':'A'}
        data.update(self.craft_label_domain())
        data.update(self.craft_ip_str())
        data.update(self.craft_ttl_and_comment())
        request = FakeRequest(json.dumps(data))
        response = commit_record(request)
        self.assertFalse('errors' in response.content)
        self.assertTrue(response.status_code, 200)
        content = json.loads(response.content)
        self.validate_return_object(content['obj_class'],
                content['obj_pk'], data)
        # Now do an update
        orig_obj_pk = content['obj_pk']
        data['pk'] = orig_obj_pk
        data.update(self.craft_label_domain())
        request = FakeRequest(json.dumps(data))
        response = commit_record(request)
        self.validate_return_object(content['obj_class'],
                content['obj_pk'], data)
        self.assertEqual(orig_obj_pk, content['obj_pk'])

    def test_TXT(self):
        data = {'rtype':'A'}
        data.update(self.craft_label_domain())
        data.update(self.craft_ip_str())
        data.update(self.craft_ttl_and_comment())
        request = FakeRequest(json.dumps(data))
        response = commit_record(request)
        self.assertFalse('errors' in response.content)
        self.assertTrue(response.status_code, 200)
        content = json.loads(response.content)
        self.validate_return_object(content['obj_class'],
                content['obj_pk'], data)
        # Now do an update
        orig_obj_pk = content['obj_pk']
        data['pk'] = orig_obj_pk
        data.update(self.craft_label_domain())
        request = FakeRequest(json.dumps(data))
        response = commit_record(request)
        self.validate_return_object(content['obj_class'],
                content['obj_pk'], data)
        self.assertEqual(orig_obj_pk, content['obj_pk'])

    def test_CNAME(self):
        data = {'rtype':'CNAME'}
        data.update(self.craft_label_domain())
        data.update({'data': random_label()})
        data.update(self.craft_ttl_and_comment())
        request = FakeRequest(json.dumps(data))
        response = commit_record(request)
        self.assertFalse('errors' in response.content)
        self.assertTrue(response.status_code, 200)
        content = json.loads(response.content)
        self.validate_return_object(content['obj_class'],
                content['obj_pk'], data)
        # Now do an update
        orig_obj_pk = content['obj_pk']
        data['pk'] = orig_obj_pk
        data.update(self.craft_label_domain())
        request = FakeRequest(json.dumps(data))
        response = commit_record(request)
        self.validate_return_object(content['obj_class'],
                content['obj_pk'], data)
        self.assertEqual(orig_obj_pk, content['obj_pk'])

    def test_PTR(self):
        data = {'rtype':'PTR'}
        data.update({'name': random_label()})
        data.update(self.craft_ip_str())
        data.update(self.craft_ttl_and_comment())
        request = FakeRequest(json.dumps(data))
        response = commit_record(request)
        self.assertFalse('errors' in response.content)
        self.assertTrue(response.status_code, 200)
        content = json.loads(response.content)
        self.validate_return_object(content['obj_class'],
                content['obj_pk'], data)
        # Now do an update
        orig_obj_pk = content['obj_pk']
        data['pk'] = orig_obj_pk
        data.update(self.craft_ip_str())
        request = FakeRequest(json.dumps(data))
        response = commit_record(request)
        self.validate_return_object(content['obj_class'],
                content['obj_pk'], data)
        self.assertEqual(orig_obj_pk, content['obj_pk'])

    def test_MX(self):
        data = {'rtype':'MX'}
        data.update(self.craft_label_domain())
        data.update(self.craft_ttl_and_comment())
        data.update(self.craft_number_dict('priority'))
        data.update(self.craft_name_dict('server'))
        request = FakeRequest(json.dumps(data))
        response = commit_record(request)
        self.assertFalse('errors' in response.content)
        self.assertTrue(response.status_code, 200)
        content = json.loads(response.content)
        self.validate_return_object(content['obj_class'],
                content['obj_pk'], data)
        # Now do an update
        orig_obj_pk = content['obj_pk']
        data['pk'] = orig_obj_pk
        data.update(self.craft_label_domain())
        request = FakeRequest(json.dumps(data))
        response = commit_record(request)
        self.validate_return_object(content['obj_class'],
                content['obj_pk'], data)
        self.assertEqual(orig_obj_pk, content['obj_pk'])

    def test_SRV(self):
        data = {'rtype':'SRV'}
        data.update({'target': random_label()})
        data.update(self.craft_label_domain())
        data['label'] = "_"+random_label()
        data.update(self.craft_ttl_and_comment())
        data.update(self.craft_number_dict('priority'))
        data.update(self.craft_number_dict('weight'))
        data.update(self.craft_number_dict('port'))
        data.update(self.craft_name_dict('target'))
        request = FakeRequest(json.dumps(data))
        response = commit_record(request)
        self.assertFalse('errors' in response.content)
        self.assertTrue(response.status_code, 200)
        content = json.loads(response.content)
        self.validate_return_object(content['obj_class'],
                content['obj_pk'], data)
        # Now do an update
        orig_obj_pk = content['obj_pk']
        data['pk'] = orig_obj_pk
        data.update(self.craft_label_domain())
        data['label'] = "_"+random_label()
        request = FakeRequest(json.dumps(data))
        response = commit_record(request)
        self.validate_return_object(content['obj_class'],
                content['obj_pk'], data)
        self.assertEqual(orig_obj_pk, content['obj_pk'])

    def test_NS(self):
        data = {'rtype':'NS'}
        data['domain'] = self.d.name
        data.update(self.craft_ttl_and_comment())
        data.update(self.craft_name_dict('server'))
        request = FakeRequest(json.dumps(data))
        response = commit_record(request)
        self.assertFalse('errors' in response.content)
        self.assertTrue(response.status_code, 200)
        content = json.loads(response.content)
        self.validate_return_object(content['obj_class'],
                content['obj_pk'], data)
        # Now do an update
        orig_obj_pk = content['obj_pk']
        data['pk'] = orig_obj_pk
        data.update(self.craft_name_dict('server'))
        request = FakeRequest(json.dumps(data))
        response = commit_record(request)
        self.validate_return_object(content['obj_class'],
                content['obj_pk'], data)
        self.assertEqual(orig_obj_pk, content['obj_pk'])


    def test_no_rtype(self):
        data = {}
        data.update(self.craft_label_domain())
        data.update(self.craft_ip_str())
        request = FakeRequest(json.dumps(data))
        self.assertRaises(Http404, commit_record, request)
        # Now do an update
        data['pk'] = ''
        request = FakeRequest(json.dumps(data))
        self.assertRaises(Http404, commit_record, request)

    def validate_return_object(self, obj_class, obj_pk, data):
        # this is a test... never do this at home
        Klass = eval(obj_class)
        obj = Klass.objects.get(pk=obj_pk)
        for k, v in data.iteritems():
            if k == "rtype":
                continue
            self.assertTrue(hasattr(obj, k))
            if k == "domain":
                self.assertEqual(getattr(obj, k).name, v)
            else:
                self.assertEqual(getattr(obj, k), v)

class FakeRequest(object):
    def __init__(self, data):
        self.raw_post_data = data
