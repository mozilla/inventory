#!/usr/bin/python
"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

import sys
import os
_base = os.path.dirname(__file__)
site_root = os.path.realpath(os.path.join(_base, '../'))
from django.core.urlresolvers import reverse
sys.path.append(site_root)
import manage
from django.test import TestCase
from django.test.client import Client
from models import KeyValue, System
from core.range.models import Range
from mozdns.domain.models import Domain
from core.network.models import Network
from mozdns.view.models import View
from core.vlan.models import Vlan
from core.site.models import Site
try:
    import json
except:
    from django.utils import simplejson as json

from inventory.systems import models
from test_utils import setup_test_environment, TestCase
setup_test_environment()


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

    def test_next_adapter_number(self):
        system = System.objects.get(id=1)
        self.assertEqual(system.get_next_adapter_number(), 2)

    def test_adapter_count(self):
        system = System.objects.get(id=1)
        adapter_count = system.get_adapter_count()
        self.assertEqual(adapter_count, 2)

    def test_adapter_exists(self):
        adapter_id = 1
        system = System.objects.get(id=1)
        self.assertEqual(True, system.check_for_adapter(1))
        self.assertEqual(False, system.check_for_adapter(3))


class SimpleTest(TestCase):
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
        res = self.client.post('/system/new/', self.system_post)

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

    def setUp(self):
        self.create_domains()
        self.client = Client()

    def test1_system_adapter_ajax_get(self):
        sys_tmp = System.objects.get(id=1)
        sys_tmp.hostname = sys_tmp.hostname + '.vlan.dc'
        sys_tmp.save()
        resp = self.client.get(
            reverse(
                "system-network-adapter-create",
                kwargs={'system_id': '1'}),
            follow=True)
        self.assertEqual(resp.status_code, 200)

    def test2_system_adapters_empty(self):
        system = System.objects.get(id=1)
        eth0 = system.staticinterface_set.all()
        self.assertEqual(len(eth0), 0)

    def test3_system_adapter_ajax_post(self):
        post_dict = {
            'interface': 'eth0.0',
            'system_id': '1',
            'hostname': 'fake-hostname',
            'is_ajax': '1',
            'range': Range.objects.all()[0].id,
            'mac_address': '00:00:00:00:00:00',
            'ip_address': '10.99.99.99',
            'enable_dhcp': 'true',
            'enable_dns': 'true',
            'enable_public': 'false',
            'enable_private': 'true', }
        sys_tmp = System.objects.get(id=1)
        sys_tmp.hostname = sys_tmp.hostname + '.vlan.dc'
        sys_tmp.save()
        resp = self.client.post(
            reverse(
                "system-network-adapter-create",
                kwargs={'system_id': '1'}),
            data=post_dict, follow=True)
        self.assertEqual(resp.status_code, 200)
        system = System.objects.get(id=1)
        eth0 = system.staticinterface_set.all()[0]
        eth0.update_attrs()
        self.assertEqual(eth0.ip_str, '10.99.99.99')
        self.assertEqual(eth0.mac, '00:00:00:00:00:00')
        self.assertEqual(eth0.ip_type, '4')
        self.assertEqual(eth0.attrs.primary, '0')
        self.assertEqual(eth0.attrs.interface_type, 'eth')
        self.assertEqual(eth0.attrs.alias, '0')

    def test4_system_adapter_ajax_post(self):
        resp = self.client.get(reverse("get-all-ranges-ajax"), follow=True)
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content)
        self.assertEqual(obj[0]['display'], 'NONE - None - 66.66.66.0/24')

    def test5_system_adapter_next_available_ip(self):
        range_id = Range.objects.get(start_str='10.99.99.1').id
        resp = self.client.get(
            reverse(
                "system-adapter-next-ip",
                kwargs={'range_id': range_id}),
            follow=True)
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content)
        self.assertEqual(obj['ip_address'], '10.99.99.1')
        self.assertEqual(obj['success'], True)

    def test6_system_adapter_ajax_get_invalid_domain(self):
        resp = self.client.get(
            reverse(
                "system-network-adapter-create",
                kwargs={'system_id': '1'}),
            follow=True)
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content)
        self.assertEqual(obj['success'], False)
        self.assertTrue(obj['error_message'].find("was not not found") != -1)

    def test7_system_adapter_add_adapter_test_ajax_all_enabled(self):
        post_dict = {
            'system_id': '1',
            'hostname': 'fake-hostname',
            'is_ajax': '1',
            'range': Range.objects.all()[0].id,
            'ip_address': '66.66.66.66',
            'mac_address': '00:00:00:00:00:00',
            'enable_dhcp': 'true',
            'enable_dns': 'true',
            'enable_public': 'true',
            'enable_private': 'true', }
        sys = System.objects.get(id=1)
        sys.hostname = sys.hostname + '.vlan.dc'
        sys.save()
        resp = self.client.post(
            reverse(
                "system-network-adapter-create",
                kwargs={'system_id': '1'}),
            data=post_dict, follow=True)
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content)
        self.assertEqual(obj['success'], True)
        sys = System.objects.get(id=1)
        eth0 = sys.staticinterface_set.all()[0]
        private = View.objects.get(name='private')
        public = View.objects.get(name='public')
        self.assertEqual(
            private.staticinterface_set.all()[0].fqdn,
            u'fake-hostname.vlan.dc.mozilla.com')
        self.assertEqual(
            private.staticinterface_set.all()[0].mac, u'00:00:00:00:00:00')
        self.assertEqual(
            private.staticinterface_set.all()[0].ip_str, u'66.66.66.66')
        self.assertEqual(
            private.staticinterface_set.all()[0].dns_enabled, True)
        self.assertEqual(
            private.staticinterface_set.all()[0].dhcp_enabled, True)

    def test8_system_adapter_add_adapter_test_ajax_dhcp_disabled(self):
        post_dict = {
            'system_id': '1',
            'hostname': 'fake-hostname',
            'range': Range.objects.all()[0].id,
            'is_ajax': '1',
            'ip_address': '66.66.66.66',
            'mac_address': '00:00:00:00:00:00',
            'enable_dhcp': 'false',
            'enable_dns': 'true',
            'enable_public': 'true',
            'enable_private': 'true', }
        sys = System.objects.get(id=1)
        sys.hostname = sys.hostname + '.vlan.dc'
        sys.save()
        resp = self.client.post(
            reverse(
                "system-network-adapter-create",
                kwargs={'system_id': '1'}),
            data=post_dict, follow=True)
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content)
        self.assertEqual(obj['success'], True)
        sys = System.objects.get(id=1)
        eth0 = sys.staticinterface_set.all()[0]
        private = View.objects.get(name='private')
        public = View.objects.get(name='public')
        self.assertEqual(
            private.staticinterface_set.all()[0].fqdn,
            u'fake-hostname.vlan.dc.mozilla.com')
        self.assertEqual(
            private.staticinterface_set.all()[0].mac,
            u'00:00:00:00:00:00')
        self.assertEqual(
            private.staticinterface_set.all()[0].ip_str,
            u'66.66.66.66')
        self.assertEqual(
            private.staticinterface_set.all()[0].dns_enabled, True)
        self.assertEqual(
            private.staticinterface_set.all()[0].dhcp_enabled, False)
        self.assertEqual(
            public.staticinterface_set.all()[0].dns_enabled, True)
        self.assertEqual(
            public.staticinterface_set.all()[0].dhcp_enabled, False)

    def test9_ajax_dhcp_enabled_public_enabled_private_disabled(self):
        post_dict = {
            'system_id': '1',
            'range': Range.objects.all()[0].id,
            'hostname': 'fake-hostname',
            'is_ajax': '1',
            'ip_address': '66.66.66.66',
            'mac_address': '00:00:00:00:00:00',
            'enable_dhcp': 'True',
            'enable_dns': 'true',
            'enable_public': 'true',
            'enable_private': 'false', }
        sys = System.objects.get(id=1)
        sys.hostname = sys.hostname + '.vlan.dc'
        sys.save()
        resp = self.client.post(
            reverse(
                "system-network-adapter-create",
                kwargs={'system_id': '1'}),
            data=post_dict, follow=True)
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content)
        self.assertEqual(obj['success'], True)
        sys = System.objects.get(id=1)
        eth0 = sys.staticinterface_set.all()[0]
        private = View.objects.get(name='private')
        public = View.objects.get(name='public')
        self.assertEqual(
            private.staticinterface_set.all()[0].fqdn,
            u'fake-hostname.vlan.dc.mozilla.com')
        self.assertEqual(
            private.staticinterface_set.all()[0].mac, u'00:00:00:00:00:00')
        self.assertEqual(
            private.staticinterface_set.all()[0].ip_str, u'66.66.66.66')
        self.assertEqual(
            private.staticinterface_set.all()[0].dns_enabled, True)
        self.assertEqual(
            private.staticinterface_set.all()[0].dhcp_enabled, True)
        self.assertEqual(public.staticinterface_set.all()[0].dns_enabled, True)

    def test10_test_ajax_dhcp_enabled_priv_enabled_pub_disabled(self):
        post_dict = {
            'system_id': '1',
            'range': Range.objects.all()[0].id,
            'hostname': 'fake-hostname',
            'is_ajax': '1',
            'ip_address': '10.99.99.10',
            'mac_address': '00:00:00:00:00:00',
            'enable_dhcp': 'True',
            'enable_dns': 'true',
            'enable_public': 'false',
            'enable_private': 'true', }
        sys = System.objects.get(id=1)
        sys.hostname = sys.hostname + '.vlan.dc'
        sys.save()
        resp = self.client.post(
            reverse(
                "system-network-adapter-create",
                kwargs={'system_id': '1'}),
            data=post_dict, follow=True)
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content)
        self.assertEqual(obj['success'], True)
        sys = System.objects.get(id=1)
        eth0 = sys.staticinterface_set.all()[0]
        private = View.objects.get(name='private')
        public = View.objects.get(name='public')
        self.assertEqual(
            private.staticinterface_set.all()[0].fqdn,
            u'fake-hostname.vlan.dc.mozilla.com')
        self.assertEqual(
            private.staticinterface_set.all()[0].mac, u'00:00:00:00:00:00')
        self.assertEqual(
            private.staticinterface_set.all()[0].ip_str, u'10.99.99.10')
        self.assertEqual(
            private.staticinterface_set.all()[0].dns_enabled, True)
        self.assertEqual(
            private.staticinterface_set.all()[0].dhcp_enabled, True)
        self.assertEqual(len(public.staticinterface_set.all()), 0)

    def test11_adapter_test_ajax_dhcp_enabled_all_dns_disabled(self):
        post_dict = {
            'system_id': '1',
            'range': Range.objects.all()[0].id,
            'hostname': 'fake-hostname',
            'is_ajax': '1',
            'ip_address': '10.99.99.10',
            'mac_address': '00:00:00:00:00:00',
            'enable_dhcp': 'True',
            'enable_dns': 'false',
            'enable_public': 'false',
            'enable_private': 'false'}
        sys = System.objects.get(id=1)
        sys.hostname = sys.hostname + '.vlan.dc'
        sys.save()
        resp = self.client.post(
            reverse(
                "system-network-adapter-create",
                kwargs={'system_id': '1'},),
            data=post_dict,
            follow=True)
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content)
        self.assertEqual(obj['success'], True)
        sys = System.objects.get(id=1)
        eth0 = sys.staticinterface_set.all()[0]
        private = View.objects.get(name='private')
        public = View.objects.get(name='public')
        self.assertEqual(len(public.staticinterface_set.all()), 0)
        self.assertEqual(len(private.staticinterface_set.all()), 0)

    def test12_test_proper_interface(self):
        post_dict = {
            'system_id': '1',
            'range': Range.objects.all()[0].id,
            'hostname': 'fake-hostname',
            'is_ajax': '1',
            'ip_address': '10.99.99.10',
            'mac_address': '00:00:00:00:00:00',
            'interface': 'eth4.1',
            'enable_dhcp': 'True',
            'enable_dns': 'false',
            'enable_public': 'false',
            'enable_private': 'false'}
        sys = System.objects.get(id=1)
        sys.hostname = sys.hostname + '.vlan.dc'
        sys.save()
        resp = self.client.post(
            reverse(
                "system-network-adapter-create",
                kwargs={'system_id': '1'},),
            data=post_dict,
            follow=True)
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content)
        self.assertEqual(obj['success'], True)
        sys = System.objects.get(id=1)
        eth0 = sys.staticinterface_set.all()[0]
        eth0.update_attrs()
        self.assertEqual(eth0.attrs.primary, u'4')
        self.assertEqual(eth0.attrs.alias, u'1')
        resp = self.client.post(
            reverse(
                "system-network-adapter-create",
                kwargs={'system_id': '1'},),
            data=post_dict,
            follow=True)
        obj = json.loads(resp.content)
        self.assertEqual(obj['success'], False)
        self.assertEqual(len(sys.staticinterface_set.all()), 1)

    def test13_bad_interface_name(self):
        post_dict = {
            'system_id': '1',
            'interface': 'asdfasfdasfdasdfasdf',
            'range': Range.objects.all()[0].id,
            'hostname': 'fake-hostname',
            'is_ajax': '1',
            'ip_address': '10.99.99.10',
            'mac_address': '00:00:00:00:00:00',
            'enable_dhcp': 'True',
            'enable_dns': 'false',
            'enable_public': 'false',
            'enable_private': 'false'}
        sys = System.objects.get(id=1)
        sys.hostname = sys.hostname + '.vlan.dc'
        sys.save()
        resp = self.client.post(
            reverse(
                "system-network-adapter-create",
                kwargs={'system_id': '1'},),
            data=post_dict,
            follow=True)
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content)
        self.assertEqual(obj['success'], False)

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

    def create_domains(self):
        private = View(name="private")
        private.save()
        public = View(name="public")
        public.save()
        Domain(name='com').save()
        Domain(name='mozilla.com').save()
        Domain(name='dc.mozilla.com').save()
        Domain(name='vlan.dc.mozilla.com').save()
        Domain(name='arpa').save()
        Domain(name='in-addr.arpa').save()
        Domain(name='10.in-addr.arpa').save()
        Domain(name='66.in-addr.arpa').save()
        vlan = Vlan(name='vlan', number=99)
        vlan.save()
        site = Site(name='dc')
        site.save()
        network = Network(network_str="10.0.0.0/8", ip_type='4')
        network2 = Network(network_str="66.66.66.0/24", ip_type='4')
        network2.update_network()
        network2.save()
        network.vlan = vlan
        network.site = site
        network.update_network()
        network.save()
        r = Range(
            start_str='10.99.99.1',
            end_str='10.99.99.254',
            network=network,)
        r.clean()
        r.save()
        r = Range(
            start_str='66.66.66.1',
            end_str='66.66.66.254',
            network=network2,)
        r.clean()
        r.save()
