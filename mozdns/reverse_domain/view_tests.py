from django.test import TestCase
from django.test.client import Client

from mozdns.reverse_domain.models import ReverseDomain
from mozdns.soa.models import SOA
from mozdns.tests.view_tests import random_byte, random_label
from settings import MOZDNS_BASE_URL

class ReverseDomainViewTests(TestCase):
    """
    Straight copy of domain view tests.
    TODO: use class inheritance and super to not reuse all the same code,
    only thing different from domain view tests is the url slug and name.
    """

    def setUp(self):
        self.url_slug = 'reverse_domain'
        soa = SOA(primary=random_label(), contact=random_label(), comment=random_label())
        self.test_obj = ReverseDomain(name=random_byte())
        self.test_obj.save()
        self.test_obj.soa = soa
        self.test_obj.save()

    def test_base_mozdns_app_reverse_domain(self):
        resp = self.client.get(MOZDNS_BASE_URL+"/%s/" % (self.url_slug),
                follow=True)
        self.assertEqual(resp.status_code, 200)

    def test_get_create_reverse_domain(self):
        resp = self.client.get(MOZDNS_BASE_URL+"/%s/create/" % (self.url_slug),
                follow=True)
        self.assertEqual(resp.status_code, 200)

    def test_post_create_reverse_domain(self):
        resp = self.client.post(MOZDNS_BASE_URL+"/%s/create/" %
                (self.url_slug), self.post_data(), follow=True)
        self.assertTrue(resp.status_code in (302, 200))

    def test_get_object_update_reverse_domain(self):
        resp = self.client.get(MOZDNS_BASE_URL+"/%s/%s/update/" %
                (self.url_slug, self.test_obj.pk), follow=True)
        self.assertEqual(resp.status_code, 200)

    def test_post_object_update_reverse_domain(self):
        resp = self.client.post(MOZDNS_BASE_URL+"/%s/%s/update/" %
                (self.url_slug,self.test_obj.pk), self.post_data(), follow=True)
        self.assertTrue(resp.status_code in (302, 200))

    def test_post_object_update_reverse_domain(self):
        resp = self.client.post(MOZDNS_BASE_URL+"/%s/%s/update/" %
                (self.url_slug,self.test_obj.pk), {'soa':''}, follow=True)
        self.assertTrue(resp.status_code in (302, 200))

    def test_get_object_details_reverse_domain(self):
        resp = self.client.get(MOZDNS_BASE_URL+"/%s/%s/" % (self.url_slug,
            self.test_obj.pk), follow=True)
        self.assertEqual(resp.status_code, 200)

    def test_get_object_delete_reverse_domain(self):
        resp = self.client.get(MOZDNS_BASE_URL+"/%s/%s/delete/" %
                (self.url_slug, self.test_obj.pk), follow=True)
        self.assertEqual(resp.status_code, 200)

    def post_data(self):
        return {
            'name': str(random_byte()),
            'soa': '1',
            'ip_type': '4',
            'delegated': 'on',
            'inherit_soa': '0',
        }
