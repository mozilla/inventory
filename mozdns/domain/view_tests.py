from django.test import TestCase
from django.test.client import Client

from mozdns.domain.models import Domain
from mozdns.soa.models import SOA
from mozdns.tests.view_tests import random_label
from settings import MOZDNS_BASE_URL

class DomainViewTests(TestCase):
    def setUp(self):
        self.url_slug = 'domain'
        soa = SOA(primary=random_label(), contact=random_label(), comment=random_label())
        self.test_obj = Domain(name=random_label())
        self.test_obj.save()
        self.test_obj.soa = soa
        self.test_obj.save()

    def test_base_mozdns_app_domain(self):
        resp = self.client.get(MOZDNS_BASE_URL+"/%s/" % (self.url_slug),
                follow=True)
        self.assertEqual(resp.status_code, 200)

    def test_get_create_domain(self):
        resp = self.client.get(MOZDNS_BASE_URL+"/%s/create/" % (self.url_slug),
                follow=True)
        self.assertEqual(resp.status_code, 200)

    def test_post_create_domain(self):
        resp = self.client.post(MOZDNS_BASE_URL+"/%s/create/" %
                (self.url_slug), self.post_data(), follow=True)
        self.assertTrue(resp.status_code in (302, 200))

    def test_get_object_update_domain(self):
        resp = self.client.get(MOZDNS_BASE_URL+"/%s/%s/update/" %
                (self.url_slug, self.test_obj.pk), follow=True)
        self.assertEqual(resp.status_code, 200)

    def test_post_object_update_domain(self):
        resp = self.client.post(MOZDNS_BASE_URL+"/%s/%s/update/" %
                (self.url_slug,self.test_obj.pk), self.post_data(), follow=True)
        self.assertTrue(resp.status_code in (302, 200))

    def test_post_object_update_domain(self):
        resp = self.client.post(MOZDNS_BASE_URL+"/%s/%s/update/" %
                (self.url_slug,self.test_obj.pk), {'soa':''}, follow=True)
        self.assertTrue(resp.status_code in (302, 200))

    def test_get_object_details_domain(self):
        resp = self.client.get(MOZDNS_BASE_URL+"/%s/%s/" % (self.url_slug,
            self.test_obj.pk), follow=True)
        self.assertEqual(resp.status_code, 200)

    def test_get_object_delete_domain(self):
        resp = self.client.get(MOZDNS_BASE_URL+"/%s/%s/delete/" %
                (self.url_slug, self.test_obj.pk), follow=True)
        self.assertEqual(resp.status_code, 200)

    def post_data(self):
        return {
            'name':random_label()
        }
