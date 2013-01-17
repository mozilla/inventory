from django.test import TestCase
from django.test.client import RequestFactory
from django.test.client import Client


from mozdns.tests.utils import random_label, random_byte
from mozdns.cname.models import CNAME
from mozdns.address_record.models import AddressRecord
from mozdns.domain.models import Domain
from mozdns.mx.models import MX
from mozdns.ptr.models import PTR
from mozdns.nameserver.models import Nameserver
from mozdns.srv.models import SRV
from mozdns.txt.models import TXT
from mozdns.sshfp.models import SSHFP
from mozdns.view.models import View

from mozdns.tests.utils import create_fake_zone


class BaseViewTestCase(object):
    record_base_url = "/mozdns/record"

    def setUp(self):
        self.rdtype = self.test_type().rdtype
        self.create_url = "{0}/create/{1}/".format(self.record_base_url,
                                                   self.rdtype)
        self.update_url_template = self.create_url + "{1}/"

        self.c = Client()
        self.factory = RequestFactory()
        self.domain = create_fake_zone("{0}.{1}.{2}".format(random_label(),
                                       random_label(), random_label()))
        View.objects.get_or_create(name='public')
        View.objects.get_or_create(name='private')

    # Add an rdtype to the dict
    def update_rdtype(self, data):
        data.update({'record_type': self.rdtype})
        return data

    def update_pk(self, data, object_):
        data.update({'record_pk': object_.pk})
        return data

    def test_update_create_and_error(self):
        # This test is just making sure that all objects can be created,
        # updated, and that the view 'record_ajax' can handle a non-valid
        # object.
        start_obj_count = self.test_type.objects.all().count()
        resp = self.c.post('/mozdns/record/record_ajax/',
                           data=self.update_rdtype(self.post_data()))
        self.assertEqual(resp.status_code, 200)
        new_obj_count = self.test_type.objects.all().count()
        self.assertEqual(start_obj_count + 1, new_obj_count)
        obj_ = self.test_type.objects.all()[0]

        # Now update. Make sure no new object was created.
        post_data = self.update_pk(self.update_rdtype(self.post_data()), obj_)
        resp = self.c.post('/mozdns/record/record_ajax/', data=post_data)
        self.assertEqual(resp.status_code, 200)
        after_update_obj_count = self.test_type.objects.all().count()
        self.assertEqual(new_obj_count, after_update_obj_count)

        # Now causes an error
        post_data = self.update_pk(self.update_rdtype(self.post_data()), obj_)
        post_data['ttl'] = 'charaters'
        resp = self.c.post('/mozdns/record/record_ajax/', data=post_data)
        after_error_obj_count = self.test_type.objects.all().count()
        self.assertEqual(new_obj_count, after_error_obj_count)
        self.assertEqual(resp.status_code, 200)

    def test_delete(self):
        start_obj_count = self.test_type.objects.all().count()
        resp = self.c.post('/mozdns/record/record_ajax/',
                           data=self.update_rdtype(self.post_data()))
        self.assertEqual(resp.status_code, 200)
        new_obj_count = self.test_type.objects.all().count()
        self.assertEqual(start_obj_count + 1, new_obj_count)

        # Get the most recent object
        new_obj = self.test_type.objects.all().order_by('pk')[0]
        self.test_type.objects.all()[0]

        resp = self.c.post('/mozdns/record/delete/{0}/{1}/'.format(
                           self.rdtype, new_obj.pk))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            0, self.test_type.objects.filter(pk=new_obj.pk).count())

        delete_obj_count = self.test_type.objects.all().count()
        self.assertEqual(start_obj_count, delete_obj_count)

    def test_bad_delete(self):
        start_obj_count = self.test_type.objects.all().count()
        resp = self.c.post('/mozdns/record/record_ajax/',
                           data=self.update_rdtype(self.post_data()))
        self.assertEqual(resp.status_code, 200)
        new_obj_count = self.test_type.objects.all().count()
        self.assertEqual(start_obj_count + 1, new_obj_count)

        # Get the most recent object
        new_obj = self.test_type.objects.all().order_by('pk')[0]
        self.test_type.objects.all()[0]

        resp = self.c.post('/mozdns/record/delete/{0}/{1}/'.format(
                           self.rdtype, new_obj.pk + 1))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            1, self.test_type.objects.filter(pk=new_obj.pk).count())


class CNAMERecordTests(BaseViewTestCase, TestCase):
    test_type = CNAME

    def post_data(self):
        return {
            'description': random_label(),
            'ttl': random_byte(),
            'fqdn': 'd' + random_label() + "." + self.domain.name,
            'target': random_label()
        }


class MXRecordTests(BaseViewTestCase, TestCase):
    test_type = MX

    def post_data(self):
        return {
            'description': random_label(),
            'ttl': random_byte(),
            'fqdn': 'e' + random_label() + "." + self.domain.name,
            'server': random_label(),
            'priority': 123,
            'ttl': 213
        }


class SRVRecordTests(BaseViewTestCase, TestCase):
    test_type = SRV

    def post_data(self):
        return {
            'description': random_label(),
            'ttl': random_byte(),
            'fqdn': "_" + random_label() + "." + self.domain.name,
            'target': random_label(),
            'priority': 2,
            'weight': 2222,
            'port': 222
        }


class TXTRecordTests(BaseViewTestCase, TestCase):
    test_type = TXT

    def post_data(self):
        return {
            'description': random_label(),
            'ttl': random_byte(),
            'fqdn': 'f' + random_label() + "." + self.domain.name,
            'txt_data': random_label()
        }


class NameserverRecordTests(BaseViewTestCase, TestCase):
    test_type = Nameserver

    def post_data(self):
        return {
            'server': 'g' + random_label(),
            'description': random_label(),
            'ttl': random_byte(),
            'domain': self.domain.pk,
        }


class SSHFPRecordTests(BaseViewTestCase, TestCase):
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


class AdderessRecordV4RecordTests(BaseViewTestCase, TestCase):
    test_type = AddressRecord

    def setUp(self):
        super(AdderessRecordV4RecordTests, self).setUp()

    def post_data(self):
        return {
            'description': random_label(),
            'ttl': random_byte(),
            'fqdn': 'i' + random_label() + "." + self.domain.name,
            'ip_str': "11.{0}.{1}.{2}".format(random_byte(), random_byte(),
                                              random_byte()),
            'ip_type': '4'
        }


class AdderessRecordV6RecordTests(BaseViewTestCase, TestCase):
    test_type = AddressRecord

    def setUp(self):
        Domain.objects.get_or_create(name='arpa')
        Domain.objects.get_or_create(name='ip6.arpa')
        Domain.objects.get_or_create(name='1.ip6.arpa')
        super(AdderessRecordV6RecordTests, self).setUp()

    def post_data(self):
        return {
            'description': random_label(),
            'ttl': random_byte(),
            'fqdn': 'j' + random_label() + "." + self.domain.name,
            'ip_str': "1000:{0}:{1}:{2}::".format(random_byte(), random_byte(),
                                                  random_byte()),
            'ip_type': '6'
        }


class PTRV6RecordTests(BaseViewTestCase, TestCase):
    test_type = PTR

    def setUp(self):
        Domain.objects.get_or_create(name='arpa')
        Domain.objects.get_or_create(name='ip6.arpa')
        Domain.objects.get_or_create(name='1.ip6.arpa')
        super(PTRV6RecordTests, self).setUp()

    def post_data(self):
        return {
            'description': 'k' + random_label(),
            'ttl': random_byte(),
            'ip_str': "1000:{0}:{1}:{2}:{3}:{4}::".format(
                random_byte(), random_byte(), random_byte(), random_byte(),
                random_byte()),
            'ip_type': '6',
            'name': random_label()
        }


class PTRV4RecordTests(BaseViewTestCase, TestCase):
    test_type = PTR

    def setUp(self):
        Domain.objects.get_or_create(name='arpa')
        Domain.objects.get_or_create(name='in-addr.arpa')
        Domain.objects.get_or_create(name='11.in-addr.arpa')
        super(PTRV4RecordTests, self).setUp()

    def post_data(self):
        return {
            'description': random_label(),
            'ttl': random_byte(),
            'ip_str': "11.{0}.{1}.{2}".format(
                random_byte(), random_byte(), random_byte()),
            'ip_type': '4',
            'name': random_label()
        }

"""
class SOARecordTests(BaseViewTestCase, TestCase):
    test_type = SOA

    def post_data(self):
        return {
            'primary': random_label() + '.' + random_label(),
            'ttl': random_byte(),
            'contact': "{0}.{1}.{2}".format(random_byte(), random_byte(),
                                            random_byte()),
            'name': random_label(),
            'comment': "{0}{1}{2}".format(random_byte(), random_byte(),
                                          random_byte())
        }
"""
