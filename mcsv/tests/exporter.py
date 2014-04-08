from django.test import TestCase, Client

from systems.tests.utils import create_fake_host
from user_systems.models import UserLicense


class CSVTests(TestCase):
    def setUp(self):
        create_fake_host(hostname='foobob1.mozilla.com', serial='1234')
        create_fake_host(hostname='foobob2.mozilla.com', serial='1235')
        create_fake_host(hostname='foobob3.mozilla.com', serial='1236')
        UserLicense.objects.create()
        self.client = Client()

    def test_get_export_page(self):
        resp = self.client.get('/en-US/csv/full_exporter/')
        self.assertEqual(resp.status_code, 200)

    def test_get_export_systems(self):
        resp = self.client.get(
            '/en-US/csv/ajax_csv_full_exporter/',
            {'class_name': 'System'}
        )
        self.assertEqual(resp.status_code, 200)

    def test_get_export_userlicences(self):
        resp = self.client.get(
            '/en-US/csv/ajax_csv_full_exporter/',
            {'class_name': 'UserLicense'}
        )
        self.assertEqual(resp.status_code, 200)
