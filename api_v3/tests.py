from system_api import SystemResource, CustomAPIResource, OperatingSystemData
from systems.models import System
from tastypie.test import ResourceTestCase
from django.core.exceptions import ValidationError
import json
from django.http import HttpRequest
from mozdns.view.models import View
from core.vlan.models import Vlan
from core.site.models import Site
from mozdns.domain.models import Domain
from core.network.models import Network
from core.range.models import Range
from systems.tests.utils import create_fake_host


class Tasty1SystemTest(ResourceTestCase):

    test_hostname = 'foobar.vlan.dc'

    def setUp(self):
        super(Tasty1SystemTest, self).setUp()

    def create_system(self, host_dict):
        create_fake_host(**host_dict)

    def test4_get_system_by_hostname(self):
        self.create_system({'hostname': self.test_hostname})
        resp = self.api_client.get(
            '/en-US/tasty/v3/system/%s/' % self.test_hostname, format='json')
        self.assertEqual(resp.status_code, 200)

    def test9_test_default_format(self):
        request = HttpRequest()
        request.method = 'GET'
        cr = CustomAPIResource()
        the_ret = cr.get_schema(request)
        self.assertEqual(
            the_ret._headers['content-type'][1],
            'application/json; charset=utf-8')

    def test10_test_format(self):
        request = HttpRequest()
        request.method = 'GET'
        request.GET['format'] = 'json'
        cr = CustomAPIResource()
        the_ret = cr.get_schema(request)
        self.assertEqual(
            the_ret._headers['content-type'][1],
            'application/json; charset=utf-8')

