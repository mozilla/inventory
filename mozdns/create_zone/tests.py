from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse

from mozdns.domain.models import Domain
from mozdns.nameserver.models import Nameserver
from mozdns.soa.models import SOA
from mozdns.tests.utils import random_label, random_byte

def localize(url):
    return '/en-US' + url

class CreateZoneTests(TestCase):

    def setUp(self):
        self.c = Client()
        Domain(name="com").save()
        Domain(name="mozilla.com").save()

    def get_post_data(self):
        """Return a valid set of data"""
        return {
            'root_domain': '{0}.{0}.mozilla.com'.format(
            random_label() + random_label()),
            'soa_primary': 'ns1.mozilla.com',
            'soa_contact': 'noc.mozilla.com',
            'nameserver_1': 'ns1.mozilla.com',
            'nameserver_2': 'ns2.mozilla.com',
            'nameserver_3': 'ns3.mozilla.com',
            'ttl_1': random_byte(),
            'ttl_2': random_byte(),
            'ttl_3': random_byte(),
        }

    def _ensure_no_change(self, post_data):
        soa_count = SOA.objects.all().count()
        domain_count = Domain.objects.all().count()
        ns_count = Nameserver.objects.all().count()
        resp = self.c.post(localize(reverse('create-zone-ajax')), post_data)
        self.assertEqual(200, resp.status_code)
        new_soa_count = SOA.objects.all().count()
        new_domain_count = Domain.objects.all().count()
        new_ns_count = Nameserver.objects.all().count()
        self.assertEqual(new_soa_count, soa_count)
        self.assertEqual(new_domain_count, domain_count)
        self.assertEqual(new_ns_count, ns_count)

    def _check_domain_tree(self, root_domain_name):
        self.assertTrue(Domain.objects.filter(name=root_domain_name))
        root_domain = Domain.objects.get(name=root_domain_name)
        self.assertFalse(root_domain.purgeable)

        p_domain = root_domain.master_domain
        while p_domain:
            self.assertEqual(None, p_domain.soa)
            p_domain = p_domain.master_domain

    def test_create_zone(self):
        soa_count = SOA.objects.all().count()
        domain_count = Domain.objects.all().count()
        ns_count = Nameserver.objects.all().count()
        post_data = self.get_post_data()
        resp = self.c.post(localize(reverse('create-zone-ajax')), post_data)
        self.assertEqual(200, resp.status_code)
        new_soa_count = SOA.objects.all().count()
        new_domain_count = Domain.objects.all().count()
        new_ns_count = Nameserver.objects.all().count()
        self.assertEqual(new_soa_count, soa_count + 1)
        self.assertEqual(new_domain_count, domain_count + 2)
        self.assertEqual(new_ns_count, ns_count + 3)
        self._check_domain_tree(post_data['root_domain'])

        # Do it again. The use of a random domain should give us a new set of
        # domain values.
        soa_count = SOA.objects.all().count()
        domain_count = Domain.objects.all().count()
        ns_count = Nameserver.objects.all().count()
        post_data = self.get_post_data()
        resp = self.c.post(localize(reverse('create-zone-ajax')), post_data)
        self.assertEqual(200, resp.status_code)
        new_soa_count = SOA.objects.all().count()
        new_domain_count = Domain.objects.all().count()
        new_ns_count = Nameserver.objects.all().count()
        self.assertEqual(new_soa_count, soa_count + 1)
        self.assertEqual(new_domain_count, domain_count + 2)
        self.assertEqual(new_ns_count, ns_count + 3)
        self._check_domain_tree(post_data['root_domain'])

    def test_more_realistic_creation(self):
        post_data = self.get_post_data()
        resp = self.c.post(localize(reverse('create-zone-ajax')), post_data)
        self.assertEqual(200, resp.status_code)
        first_root_domain = post_data['root_domain']
        self._check_domain_tree(first_root_domain)

        # Now create a new zone under the created zone. Make sure the tree
        # under the new zone is preserved.

        second_root_domain = "{0}.{1}".format(
            random_label(), first_root_domain)
        post_data['root_domain'] = second_root_domain
        resp = self.c.post(localize(reverse('create-zone-ajax')), post_data)
        self.assertEqual(200, resp.status_code)
        self._check_domain_tree(first_root_domain)
        self.assertTrue(Domain.objects.filter(name=second_root_domain))
        root_domain = Domain.objects.get(name=second_root_domain)
        self.assertFalse(root_domain.purgeable)
        self.assertFalse(root_domain.master_domain.purgeable)

        self.assertNotEqual(None, root_domain.soa)
        self.assertFalse(None, root_domain.master_domain.soa)

    def test_create_zone_bad_soa(self):
        post_data = self.get_post_data()
        post_data['root_domain'] = ''
        self._ensure_no_change(post_data)

        # Try a bad primary
        post_data = self.get_post_data()
        post_data['soa_primary'] = 'adsf..afds'
        self._ensure_no_change(post_data)

        # Try a bad contact
        post_data = self.get_post_data()
        post_data['soa_contact'] = 'adsf.#afds'
        self._ensure_no_change(post_data)

        # Try a missing contact
        post_data = self.get_post_data()
        del post_data['soa_contact']
        self._ensure_no_change(post_data)

    def test_create_zone_bad_ns(self):
        # Bad ns server
        post_data = self.get_post_data()
        post_data['nameserver_1'] = '..'
        self._ensure_no_change(post_data)

        # Bad ttl
        post_data = self.get_post_data()
        post_data['ttl_1'] = 'asdf'
        self._ensure_no_change(post_data)

        # No glue
        post_data = self.get_post_data()
        post_data['nameserver_3'] = 'ns1.' + post_data['root_domain']
        self._ensure_no_change(post_data)

    def test_create_tld(self):
        # Try a bad primary
        post_data = self.get_post_data()
        post_data['root_domain'] = 'asdf'
        post_data['soa_primary'] = 'adsf..'
        self._ensure_no_change(post_data)
