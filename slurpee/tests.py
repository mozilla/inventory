from django.test import Client, TestCase

from slurpee.models import ExternalData
from slurpee.constants import P_OVERLAY

from systems.tests.utils import create_fake_host

import simplejson as json


class ExternalDataTests(TestCase):
    def setUp(self):
        serial = 'asdf'
        self.external_serial = serial + 'asdf'
        self.s = create_fake_host(
            hostname='fakehost.mozilla.com', serial=serial
        )
        ExternalData.objects.create(
            system=self.s,
            name='serial',
            source_name='serial',
            data=self.external_serial,  # conflict data
            source='foo-source',
            policy=P_OVERLAY
        )
        self.c = Client()

    def test_conflicts_page(self):
        """Animals that can speak are correctly identified"""
        resp = self.c.get(
            "/slurpee/conflicts/?search={0}".format(self.s.hostname),
            follow=True
        )
        self.assertEqual(200, resp.status_code)

    def test_sync(self):
        """Animals that can speak are correctly identified"""
        resp = self.c.post("/en-US/systems/sync_external_data/", {
            'attr': 'serial',
            'source': 'foo-source',
            'system_pk': self.s.pk
        })
        self.assertEqual(200, resp.status_code, json.loads(resp.content))
        # Refresh the object cache
        s = self.s.__class__.objects.get(pk=self.s.pk)
        self.assertEqual(self.external_serial, s.serial)
