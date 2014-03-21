import datetime
import time

try:
    import json
except:
    import simplejson as json

from django.core.exceptions import ValidationError
from django.test import TestCase, TransactionTestCase
from django.test.client import Client

from systems.models import System
from mozdns.domain.models import Domain
from mozdns.view.models import View
from mozdns.tests.utils import create_fake_zone
from core.range.models import Range
from core.network.models import Network
from core.vlan.models import Vlan
from core.site.models import Site
from core.group.models import Group

from systems import models
from systems.tests.utils import create_fake_host
from test_utils import setup_test_environment
from decommission.views import decommission_

setup_test_environment()


class LocalizeUtils(object):
    def localize_url(self, url):
        if 'en-US' not in url:
            if 'http://testserver/' in url:
                url = url.replace(
                    'http://testserver/', 'http://testserver/en-US/'
                )
            else:
                url = '/en-US' + url
        return url


class SystemDatagridTest(TestCase):
    fixtures = ['testdata.json']

    def setUp(self):
        self.client = Client()

    def test_index(self):
        resp = self.client.get(
            "/en-US/systems/list_all_systems_ajax/?_=1326311056 \
            872&sEcho=1&iColumns=3&sColumns=&iDisplayStart=0 \
            &iDisplayLength=10&sSearch=&bRegex=false \
            &sSearch_0=&bRegex_0=false&bSearchable_0=true \
            &sSearch_1=&bRegex_1=false&bSearchable_1=true \
            &sSearch_2=&bRegex_2=false&bSearchable_2=true \
            &iSortingCols=1&iSortCol_0=0&sSortDir_0=asc \
            &bSortable_0=true&bSortable_1=true&bSortable_2=false",
            follow=True)
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content)
        obj = obj['aaData']
        self.assertEqual(len(obj), 2)
        self.assertEqual(obj[0][0], '2,fake-hostname1')

    def test_blanket_search(self):
        search_url = "/en-US/systems/list_all_systems_ajax/\
?_=1326311056872&sEcho=1&iColumns=3&sColumns=\
&iDisplayStart=0&iDisplayLength=10 &sSearch=fake-hostname\
&bRegex=false&sSearch_0=&bRegex_0=false&bSearchable_0=true\
&sSearch_1=&bRegex_1=false&bSearchable_1=true\
&sSearch_2=&bRegex_2=false&bSearchable_2=true&iSortingCols=1\
&iSortCol_0=0&sSortDir_0=asc&bSortable_0=true\
&bSortable_1=true&bSortable_2=false"
        resp = self.client.get(search_url, follow=True)
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content)
        obj = obj['aaData']
        self.assertEqual(len(obj), 2)
        self.assertEqual(obj[0][0], '2,fake-hostname1')

    def test_specific_search(self):
        search_url = "/en-US/systems/list_all_systems_ajax/\
?_=1326317772224&sEcho=4&iColumns=8&sColumns=\
&iDisplayStart=0&iDisplayLength=10&mDataProp_0=0\
&mDataProp_1=1&mDataProp_2=2&mDataProp_3=3&mDataProp_4=4\
&mDataProp_5=5&mDataProp_6=6&mDataProp_7=7\
&sSearch=fake-hostname2&bRegex=false&sSearch_0=\
&bRegex_0=false&bSearchable_0=true&sSearch_1=\
&bRegex_1=false&bSearchable_1=true&sSearch_2=&bRegex_2=false\
&bSearchable_2=true&sSearch_3=&bRegex_3=false\
&bSearchable_3=true&sSearch_4=&bRegex_4=false\
&bSearchable_4=true&sSearch_5=&bRegex_5=false\
&bSearchable_5=true&sSearch_6=&bRegex_6=false\
&bSearchable_6=true&sSearch_7=&bRegex_7=false\
&bSearchable_7=true&iSortingCols=1&iSortCol_0=0\
&sSortDir_0=asc&bSortable_0=true&bSortable_1=true\
&bSortable_2=true&bSortable_3=true&bSortable_4=true\
&bSortable_5=true&bSortable_6=true&bSortable_7=false"

        resp = self.client.get(search_url, follow=True)
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content)
        obj = obj['aaData']
        self.assertEqual(len(obj), 1)
        self.assertEqual(obj[0][0], '1,fake-hostname2')

    def test_failed_search(self):
        resp = self.client.get(
            "/en-US/systems/list_all_systems_ajax/?_=1326317772224&sEcho=4 \
                    &iColumns=8&sColumns=&iDisplayStart=0&iDisplayLength=10 \
                    &mDataProp_0=0&mDataProp_1=1&mDataProp_2=2&mDataProp_3=3 \
                    &mDataProp_4=4&mDataProp_5=5&mDataProp_6=6&mDataProp_7=7 \
                    &sSearch=asdfasdfasdf&bRegex=false&sSearch_0= \
                    &bRegex_0=false&bSearchable_0=true&sSearch_1= \
                    &bRegex_1=false&bSearchable_1=true&sSearch_2= \
                    &bRegex_2=false&bSearchable_2=true&sSearch_3=& \
                    bRegex_3=false&bSearchable_3=true&sSearch_4= \
                    &bRegex_4=false&bSearchable_4=true&sSearch_5= \
                    &bRegex_5=false&bSearchable_5=true&sSearch_6= \
                    &bRegex_6=false&bSearchable_6=true&sSearch_7= \
                    &bRegex_7=false&bSearchable_7=true&iSortingCols=1 \
                    &iSortCol_0=0&sSortDir_0=asc&bSortable_0=true \
                    &bSortable_1=true&bSortable_2=true&bSortable_3=true \
                    &bSortable_4=true&bSortable_5=true&bSortable_6=true \
                    &bSortable_7=false", follow=True)
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content)
        obj = obj['aaData']
        self.assertEqual(len(obj), 0)


class BlankTest(TestCase):
    fixtures = ['testdata.json']

    def setUp(self):
        self.client = Client()

    def test_get_adapter_names(self):
        system = System.objects.get(id=1)
        self.assertEqual(len(system.get_nic_names()), 2)

    def test_adapter_name_exists(self):
        system = System.objects.get(id=1)
        self.assertEqual(system.check_for_adapter_name('nic1'), True)
        self.assertEqual(system.check_for_adapter_name('nic0'), True)
        self.assertEqual(system.check_for_adapter_name('nic2'), False)

    def test_adapter_count(self):
        system = System.objects.get(id=1)
        adapter_count = system.get_adapter_count()
        self.assertEqual(adapter_count, 2)

    def test_adapter_exists(self):
        system = System.objects.get(id=1)
        self.assertEqual(True, system.check_for_adapter(1))
        self.assertEqual(False, system.check_for_adapter(3))


class SystemTest(TestCase, LocalizeUtils):
    fixtures = ['testdata.json']
    system_post = {
        'Submit': 'Save',
        'allocation': '1',
        'asset_tag': '',
        'change_password_day': '3',
        'change_password_month': '2',
        'change_password_year': '2011',
        'hostname': 'test system 1',
        'licenses': '121-21-111-555-5555',
        'notes': 'A bunch of notes.',
        'oob_ip': '192.168.1.11',
        'oob_switch_port': '101.22',
        'operating_system': '1',
        'patch_panel_port': '101',
        'purchase_date_day': '4',
        'purchase_date_month': '4',
        'purchase_date_year': '2011',
        'purchase_price': '$101.2',
        'rack_order': '1.00',
        'serial': '39993',
        'server_model': '1',
        'switch_ports': '101.02',
        'system_rack': '1',
        'system_status': '',
    }

    def setUp(self):
        self.client = Client()

    def test_system_creation(self):
        self.client.post('/system/new/', self.system_post)

    def test_system_update(self):
        s = create_fake_host(hostname='foo.mozilla.com')
        new_hostname = 'foo1.mozilla.com'
        post_data = {
            'hostname': new_hostname
        }
        resp = self.client.post(
            self.localize_url(s.get_edit_url()), post_data, follow=True
        )
        self.assertTrue(resp.status_code in (200, 201))
        s = System.objects.get(pk=s.pk)
        self.assertEqual(s.hostname, new_hostname)

    def test_failed_validation(self):
        # Make sure that if a ValidationError is raised that we get a 200 and
        # not an ISE
        s = create_fake_host(hostname='foo.mozilla.com')
        # Bad warranty dates should cause a VE
        post_data = {
            'warrant_start_year': '2013',
            'warrant_start_month': '12',
            'warrant_start_day': '12',
            'warrant_end_year': '2012',
            'warrant_end_month': '12',
            'warrant_end_dat': '12'
        }
        resp = self.client.post(
            self.localize_url(s.get_edit_url()), post_data, follow=True
        )
        self.assertTrue(resp.status_code in (200, 201))
        s = System.objects.get(pk=s.pk)
        # Hostname should be the same
        self.assertEqual(s.hostname, 'foo.mozilla.com')

    def test_quicksearch_by_hostname(self):
        resp = self.client.post(
            "/en-US/systems/quicksearch/",
            {'quicksearch': 'fake-hostname2', 'is_test': 'True'},
            follow=True)
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content)
        self.assertEqual(1, obj[0]['pk'])
        self.assertEqual('fake-hostname2', obj[0]['fields']['hostname'])

    def test_quicksearch_by_asset_tag(self):
        resp = self.client.post(
            "/en-US/systems/quicksearch/",
            {'quicksearch': '65432',
                'is_test': 'True'})
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content)
        self.assertEqual(1, obj[0]['pk'])
        self.assertEqual('fake-hostname2', obj[0]['fields']['hostname'])

    def test_server_models_index(self):
        resp = self.client.get("/en-US/systems/server_models/", follow=True)
        self.assertEqual(resp.status_code, 200)

    def test_create(self):
        create_fake_host(hostname='foo.mozilla.com')

    def test_bad_warranty(self):
        s = create_fake_host(hostname='foo.mozilla.com', save=False)
        earlier = datetime.date.fromtimestamp(time.time() - 60 * 60 * 24 * 7)
        now = datetime.datetime.now()
        s.warranty_start = now
        s.warranty_end = earlier
        self.assertRaises(ValidationError, s.save)


class ServerModelTest(TestCase):
    fixtures = ['testdata.json']

    def setUp(self):
        self.client = Client()

    def test_update_ajax_page_exists(self):
        resp = self.client.get(
            "/en-US/systems/server_models/create_ajax/",
            follow=True)
        self.assertEqual(resp.status_code, 200)

    def test_server_models_count(self, the_count=1):
        self.assertEqual(models.ServerModel.objects.count(), the_count)

    def test_server_models_count_after_post(self):
        self.test_server_models_count(1)
        self.client.post(
            "/en-US/systems/server_models/create_ajax/",
            {'model': 'test', 'vendor': 'vendor'},
            follow=True)
        self.test_server_models_count(2)
        self.assertEqual(models.ServerModel.objects.all()[0].model, 'DL360')
        self.assertEqual(models.ServerModel.objects.all()[0].vendor, 'HP')
        self.assertEqual(models.ServerModel.objects.all()[1].model, 'test')
        self.assertEqual(models.ServerModel.objects.all()[1].vendor, 'vendor')


class SystemAdapterTest(TestCase):
    fixtures = ['testdata.json']

    def test14_system_get_key_value_adapter(self):
        system = System.objects.get(id=1)
        na = system.get_next_key_value_adapter()
        self.assertEqual(na['num'], 0)
        self.assertEqual(na['mac_address'], '00:00:00:00:00:AA')
        self.assertEqual(na['dhcp_scope'], 'phx-vlan73')
        self.assertEqual(na['ipv4_address'], '10.99.32.1')

    def test15_system_delete_key_value_adapter(self):
        system = System.objects.get(id=1)
        na = system.get_next_key_value_adapter()
        self.assertEqual(na['num'], 0)
        system.delete_key_value_adapter_by_index(0)
        na = system.get_next_key_value_adapter()
        self.assertEqual(na['num'], 1)


class SystemInterfaceTest(TransactionTestCase):
    fixtures = ['testdata.json']

    def setUp(self):
        self.client = Client()
        self.private = View.objects.create(name="private")
        self.public = View.objects.create(name="public")
        self.group = Group.objects.create(name='foobar')
        self.d0 = create_fake_zone("dc.mozilla.com", suffix="")
        self.s = self.d0.soa
        self.d1 = Domain.objects.create(
            name='vlan.dc.mozilla.com', soa=self.d0.soa
        )
        Domain(name='arpa').save()
        Domain(name='in-addr.arpa').save()

        # Create Reverse Domains
        self.rd0 = create_fake_zone("10.in-addr.arpa", suffix="")
        self.rd1 = create_fake_zone("66.in-addr.arpa", suffix="")

        self.vlan = Vlan.objects.create(name='vlan', number=99)
        self.site = Site.objects.create(name='dc')
        self.network = Network.objects.create(
            network_str="10.0.0.0/8", ip_type='4', vlan=self.vlan,
            site=self.site
        )
        self.network2 = Network.objects.create(
            network_str="66.66.66.0/24", ip_type='4', vlan=self.vlan,
            site=self.site
        )
        self.r1 = Range.objects.create(
            start_str='10.99.99.1', end_str='10.99.99.254',
            network=self.network
        )
        self.r2 = Range.objects.create(
            start_str='66.66.66.1', end_str='66.66.66.254',
            network=self.network2
        )
        self.system = create_fake_host(
            hostname='host1.vlan.dc.mozilla.com'
        )


class SystemDecommission(TestCase):
    def setUp(self):
        self.client = Client()
        models.SystemStatus.objects.create(status='decommissioned')

    def tearDown(self):
        models.SystemStatus.objects.all().delete()

    def test_allocation(self):
        s = create_fake_host(hostname='fooasdfasdf.mozilla.com')
        self.assertNotEqual('decommissioned', s.system_status.status)
        self.assertTrue(s.allocation)
        decommission_({'systems': [s.hostname]}, load_json=False)

        s = System.objects.get(pk=s.pk)
        self.assertEqual('decommissioned', s.system_status.status)
        self.assertFalse(s.allocation)
