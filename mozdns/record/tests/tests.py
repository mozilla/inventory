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
from core.registration.static.models import StaticReg
from systems.tests.utils import create_fake_host

from mozdns.tests.utils import create_fake_zone


class BaseRecordTestCase(object):
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
        self.second_domain = create_fake_zone("{0}.{1}.{2}".format(
            random_label(), random_label(), random_label())
        )
        self.public_view = View.objects.get_or_create(name='public')[0]
        self.private_view = View.objects.get_or_create(name='private')[0]
        self.system = create_fake_host(hostname="foo.bar.com")
        self.system.save()

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
        resp = self.c.post('/en-US/mozdns/record/record_ajax/',
                           data=self.update_rdtype(self.post_data()))
        self.assertEqual(resp.status_code, 200)
        new_obj_count = self.test_type.objects.all().count()
        self.assertEqual(start_obj_count + 1, new_obj_count)
        obj_ = self.test_type.objects.all()[0]

        # Now update. Make sure no new object was created.
        post_data = self.update_pk(self.update_rdtype(self.post_data()), obj_)
        resp = self.c.post('/en-US/mozdns/record/record_ajax/', data=post_data)
        self.assertEqual(resp.status_code, 200)
        after_update_obj_count = self.test_type.objects.all().count()
        self.assertEqual(new_obj_count, after_update_obj_count)

        # Now causes an error
        post_data = self.update_pk(self.update_rdtype(self.post_data()), obj_)
        post_data['ttl'] = 'charaters'
        resp = self.c.post('/en-US/mozdns/record/record_ajax/', data=post_data)
        after_error_obj_count = self.test_type.objects.all().count()
        self.assertEqual(new_obj_count, after_error_obj_count)
        self.assertEqual(resp.status_code, 200)

    def test_delete(self):
        start_obj_count = self.test_type.objects.all().count()
        resp = self.c.post('/en-US/mozdns/record/record_ajax/',
                           data=self.update_rdtype(self.post_data()))
        self.assertEqual(resp.status_code, 200)
        new_obj_count = self.test_type.objects.all().count()
        self.assertEqual(start_obj_count + 1, new_obj_count)

        # Get the most recent object
        new_obj = self.test_type.objects.all().order_by('pk')[0]
        self.test_type.objects.all()[0]

        resp = self.c.post('/en-US/mozdns/record/delete/{0}/{1}/'.format(
                           self.rdtype, new_obj.pk))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            0, self.test_type.objects.filter(pk=new_obj.pk).count())

        delete_obj_count = self.test_type.objects.all().count()
        self.assertEqual(start_obj_count, delete_obj_count)

    def test_bad_delete(self):
        start_obj_count = self.test_type.objects.all().count()
        resp = self.c.post('/en-US/mozdns/record/record_ajax/',
                           data=self.update_rdtype(self.post_data()))
        self.assertEqual(resp.status_code, 200)
        new_obj_count = self.test_type.objects.all().count()
        self.assertEqual(start_obj_count + 1, new_obj_count)

        # Get the most recent object
        new_obj = self.test_type.objects.all().order_by('pk')[0]
        self.test_type.objects.all()[0]

        resp = self.c.post('/en-US/mozdns/record/delete/{0}/{1}/'.format(
                           self.rdtype, new_obj.pk + 1))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            1, self.test_type.objects.filter(pk=new_obj.pk).count())

    def get_domain_and_post_data(self):
        # This is different for classes that have ips instead of fqdns
        domain_name = "{0}.{1}.{2}.{3}.com".format(
            random_label(), random_label(), random_label(), random_label()
        )
        root_domain = create_fake_zone(domain_name, suffix="")
        post_data = self.post_data()
        post_data = self.update_rdtype(post_data)
        # Get the '_' in SRV records
        post_data['fqdn'] = post_data['fqdn'][0] + "asdf.asdf." + domain_name
        return root_domain, post_data

    def test_no_ns_in_view(self, gdpd=None):
        if gdpd is None:
            gdpd = self.get_domain_and_post_data
        root_domain, post_data = gdpd()
        ns = root_domain.nameserver_set.all()[0]
        ns.views.remove(self.public_view)
        ns.views.remove(self.private_view)
        # We now have a zone with nameservers that aren't in any views. No
        # record should be allowed to be in the view

        start_obj_count = self.test_type.objects.all().count()
        post_data['views'] = [self.public_view.pk]
        resp = self.c.post('/en-US/mozdns/record/record_ajax/', data=post_data)
        self.assertEqual(resp.status_code, 200)
        new_obj_count = self.test_type.objects.all().count()
        # Nothing should have been created
        self.assertEqual(start_obj_count, new_obj_count)

        ns.views.add(self.public_view)
        # Okay, we should be able to add to the public view now
        start_obj_count = self.test_type.objects.all().count()
        resp = self.c.post('/en-US/mozdns/record/record_ajax/', data=post_data)
        new_obj_count = self.test_type.objects.all().count()
        self.assertEqual(start_obj_count + 1, new_obj_count)

    def make_rr(self, first_data, second_data):
        second_data['fqdn'] = first_data['fqdn']  # make fqdn the same

    def make_not_rr(self, first_obj, second_obj):
        # I'm assuming make_rr has already been called on these objects to they
        # should already by rr. changing one should make them not rr.
        first_obj.label = first_obj.label + 'asdf'

    def assert_rr(self, first_obj, second_obj):
        self.assertEqual(first_obj.fqdn, second_obj.fqdn)

    def test_rr_missmatched_ttl_post_create(self):
        # Create a new object with a non-default ttl, then create a second
        # object with the same fqdn and make sure the ttl is the same as the
        # first.  Then change the second object's ttl and make sure the first
        # objects' ttl is the same.

        start_obj_count = self.test_type.objects.all().count()
        first_data = self.update_rdtype(self.post_data())
        first_data['ttl'] = 999  # set the ttl
        resp = self.c.post('/en-US/mozdns/record/record_ajax/',
                           data=first_data)
        self.assertEqual(resp.status_code, 200)
        first_new_obj_count = self.test_type.objects.all().count()
        self.assertEqual(start_obj_count + 1, first_new_obj_count)
        first_obj = self.test_type.objects.all().order_by('-pk')[0]

        second_data = self.update_rdtype(self.post_data())
        self.make_rr(first_data, second_data)  # yay side effects
        second_data['ttl'] = 420  # Make the fqdn different than the first
        resp = self.c.post('/en-US/mozdns/record/record_ajax/',
                           data=second_data)
        self.assertEqual(resp.status_code, 200)
        second_new_obj_count = self.test_type.objects.all().count()
        self.assertEqual(first_new_obj_count + 1, second_new_obj_count)
        first_obj.save()
        second_obj = self.test_type.objects.all().order_by('-pk')[0]
        self.assertEqual(first_obj.ttl, second_obj.ttl)

        # now change second_obj's ttl and make sure it changed firsts'.
        second_obj.ttl = 888
        second_obj.save()

        first_obj = self.test_type.objects.get(pk=first_obj.pk)  # refresh
        self.assertEqual(first_obj.ttl, second_obj.ttl)

        # Then make the fqdn's not match to make sure no ttl's are changed
        self.make_not_rr(first_obj, second_obj)
        first_obj.save()
        first_obj.ttl = 1234
        first_obj.save()

        second_obj = self.test_type.objects.get(pk=second_obj.pk)  # refresh
        self.assertEqual(second_obj.ttl, 888)  # nothing should have changed


class CNAMERecordTests(BaseRecordTestCase, TestCase):
    test_type = CNAME

    def test_rr_missmatched_ttl_post_create(self):
        # Round Robin CNAMEs are not allowed since they are singleton records
        pass

    def post_data(self):
        return {
            'description': random_label(),
            'ttl': random_byte(),
            'fqdn': 'd' + random_label() + "." + self.domain.name,
            'target': random_label()
        }


class MXRecordTests(BaseRecordTestCase, TestCase):
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


class SRVRecordTests(BaseRecordTestCase, TestCase):
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


class TXTRecordTests(BaseRecordTestCase, TestCase):
    test_type = TXT

    def post_data(self):
        return {
            'description': random_label(),
            'ttl': random_byte(),
            'fqdn': 'f' + random_label() + "." + self.domain.name,
            'txt_data': random_label()
        }


class NameserverRecordTests(BaseRecordTestCase, TestCase):
    test_type = Nameserver

    def make_rr(self, first_data, second_data):
        second_data['domain'] = first_data['domain']  # make ip_str the same

    def make_not_rr(self, first_obj, second_obj):
        first_obj.domain = self.second_domain

    def assert_rr(self, first_obj, second_obj):
        self.assertEqual(first_obj.domain, second_obj.domain)

    def post_data(self):
        return {
            'server': 'g' + random_label(),
            'description': random_label(),
            'ttl': random_byte(),
            'domain': self.domain.pk,
        }

    def test_no_ns_in_view(self):
        root_domain = create_fake_zone("asdfdjhjd")
        ns = root_domain.nameserver_set.all()[0]

        cn = CNAME(label='asdf', domain=root_domain, target='test.com')
        cn.full_clean()
        cn.save()
        cn.views.add(self.public_view)

        self.assertTrue(ns.domain.soa == cn.domain.soa)

        # We now should have a nameserver and a cname in the public view. The
        # nameserver should not be allowed to disable it's public view

        # Try to remove the public view
        self.assertTrue(self.public_view in ns.views.all())
        self.assertTrue(self.private_view in ns.views.all())
        post_data = self.update_rdtype(self.post_data())
        post_data['domain'] = ns.domain.pk
        post_data['views'] = [self.private_view.pk]
        post_data['record_pk'] = ns.pk
        resp = self.c.post('/en-US/mozdns/record/record_ajax/',
                           data=post_data)
        self.assertEqual(resp.status_code, 200)
        # Make sure it's still there
        ns = Nameserver.objects.get(pk=ns.pk)  # fetch
        # Make sure the view is still there
        # The clean method should prevent it from being deleted
        self.assertTrue(self.public_view in ns.views.all())

        # Try to remove the private view
        # This should be allowed
        self.assertTrue(self.public_view in ns.views.all())
        post_data = self.update_rdtype(self.post_data())
        post_data['views'] = [self.public_view.pk]
        post_data['record_pk'] = ns.pk
        resp = self.c.post('/en-US/mozdns/record/record_ajax/',
                           data=post_data)
        self.assertEqual(resp.status_code, 200)
        # Make sure it's still there
        ns = Nameserver.objects.get(pk=ns.pk)  # fetch
        # Make sure the view is still there
        # The clean method should prevent it from being deleted
        self.assertTrue(self.private_view not in ns.views.all())


class SSHFPRecordTests(BaseRecordTestCase, TestCase):
    test_type = SSHFP

    def post_data(self):
        return {
            'description': random_label(),
            'ttl': random_byte(),
            'fqdn': 'h' + random_label() + "." + self.domain.name,
            'algorithm_number': 1,
            'fingerprint_type': 1,
            'key': 'fe400b7ac08e79f64fab45cdf866e7672fd3c45c'
        }


class AdderessRecordV4RecordTests(BaseRecordTestCase, TestCase):
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


class AdderessRecordV6RecordTests(BaseRecordTestCase, TestCase):
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


class BasePTRTests(BaseRecordTestCase):
    # PTRs need their own because they don't have fqdn's

    def make_rr(self, first_data, second_data):
        second_data['ip_str'] = first_data['ip_str']  # make ip_str the same

    def make_not_rr(self, first_obj, second_obj):
        first_obj.ip_str = self.post_data()['ip_str']
        second_obj.ip_str = self.post_data()['ip_str']

    def assert_rr(self, first_obj, second_obj):
        self.assertEqual(first_obj.ip_str, second_obj.ip_str)


class PTRV6RecordTests(BasePTRTests, TestCase):
    test_type = PTR

    def get_domain_and_post_data(self):
        # This is different for classes that have ips instead of fqdns
        domain_name = "9.ip6.arpa"
        root_domain = create_fake_zone(domain_name, suffix="")
        post_data = self.post_data()
        post_data = self.update_rdtype(post_data)
        # Get the '_' in SRV records
        post_data['ip_str'] = '9000::df12'
        return root_domain, post_data

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


class PTRV4RecordTests(BasePTRTests, TestCase):
    test_type = PTR

    def get_domain_and_post_data(self):
        # This is different for classes that have ips instead of fqdns
        domain_name = "2.in-addr.arpa"
        root_domain = create_fake_zone(domain_name, suffix="")
        post_data = self.post_data()
        post_data = self.update_rdtype(post_data)
        # Get the '_' in SRV records
        post_data['ip_str'] = '2.10.1.1'
        return root_domain, post_data

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


class SREGV4RecordTests(BaseRecordTestCase, TestCase):
    test_type = StaticReg

    def get_reverse_domain_and_post_data(self):
        # This is different for classes that have ips instead of fqdns
        domain_name = "123.in-addr.arpa"
        root_domain = create_fake_zone(domain_name, suffix="")
        post_data = self.post_data()
        post_data = self.update_rdtype(post_data)
        # Get the '_' in SRV records
        post_data['ip_str'] = '123.10.1.1'
        return root_domain, post_data

    def test_no_ns_in_view_reverse(self):
        self.test_no_ns_in_view(gdpd=self.get_reverse_domain_and_post_data)

    def setUp(self):
        Domain.objects.get_or_create(name='arpa')
        Domain.objects.get_or_create(name='in-addr.arpa')
        Domain.objects.get_or_create(name='4.in-addr.arpa')
        super(SREGV4RecordTests, self).setUp()

    def post_data(self):
        return {
            'description': random_label(),
            'ttl': random_byte(),
            'interface_name': 'eth0',
            'fqdn': 'sreg' + random_label() + "." + self.domain.name,
            'ip_str': "4.{0}.{1}.{2}".format(
                random_byte(), random_byte(), random_byte()),
            'ip_type': '4',
            'system': self.system.pk,
            'mac': '00:11:22:33:44:55'
        }


class SREGV6RecordTests(BaseRecordTestCase, TestCase):
    test_type = StaticReg

    def get_reverse_domain_and_post_data(self):
        # This is different for classes that have ips instead of fqdns
        domain_name = "3.ip6.arpa"
        root_domain = create_fake_zone(domain_name, suffix="")
        post_data = self.post_data()
        post_data = self.update_rdtype(post_data)
        # Get the '_' in SRV records
        post_data['ip_str'] = '3000::df12'
        return root_domain, post_data

    def test_no_ns_in_view_reverse(self):
        self.test_no_ns_in_view(gdpd=self.get_reverse_domain_and_post_data)

    def setUp(self):
        Domain.objects.get_or_create(name='arpa')
        Domain.objects.get_or_create(name='ip6.arpa')
        Domain.objects.get_or_create(name='8.ip6.arpa')
        super(SREGV6RecordTests, self).setUp()

    def post_data(self):
        return {
            'description': 'k' + random_label(),
            'ttl': random_byte(),
            'interface_name': 'eth0',
            'fqdn': 'sreg' + random_label() + "." + self.domain.name,
            'ip_str': "8000:{0}:{1}:{2}:{3}:{4}::".format(
                random_byte(), random_byte(), random_byte(), random_byte(),
                random_byte()),
            'system': self.system.pk,
            'ip_type': '6',
            'mac': '00:11:22:33:44:55'
        }

"""
class SOARecordTests(BaseRecordTestCase, TestCase):
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
