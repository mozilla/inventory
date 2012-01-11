#!/usr/bin/python
"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from django.test import TestCase
from django.test.client import Client
import manage
from models import KeyValue, System
try:
    import json
except:
    from django.utils import simplejson as json

from inventory.systems import models
from test_utils import setup_test_environment,TestCase
setup_test_environment()
class SystemDatagridTest(TestCase):
    fixtures = ['testdata.json']
    def setUp(self):
        self.client = Client()

    def test_index(self):
        resp = self.client.get("/en-US/systems/list_all_systems_ajax/?_=1326311056872&sEcho=1&iColumns=3&sColumns=&iDisplayStart=0&iDisplayLength=10&sSearch=&bRegex=false&sSearch_0=&bRegex_0=false&bSearchable_0=true&sSearch_1=&bRegex_1=false&bSearchable_1=true&sSearch_2=&bRegex_2=false&bSearchable_2=true&iSortingCols=1&iSortCol_0=0&sSortDir_0=asc&bSortable_0=true&bSortable_1=true&bSortable_2=false", follow=True)
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content)
        obj = obj['aaData']
        self.assertEqual(len(obj),2)
        self.assertEqual(obj[0][0], '2,fake-hostname1')

    def test_blanket_search(self):
        resp = self.client.get("/en-US/systems/list_all_systems_ajax/?_=1326311056872&sEcho=1&iColumns=3&sColumns=&iDisplayStart=0&iDisplayLength=10&sSearch=fake-hostname&bRegex=false&sSearch_0=&bRegex_0=false&bSearchable_0=true&sSearch_1=&bRegex_1=false&bSearchable_1=true&sSearch_2=&bRegex_2=false&bSearchable_2=true&iSortingCols=1&iSortCol_0=0&sSortDir_0=asc&bSortable_0=true&bSortable_1=true&bSortable_2=false", follow=True)
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content)
        obj = obj['aaData']
        self.assertEqual(len(obj),2)
        self.assertEqual(obj[0][0], '2,fake-hostname1')

    def test_specific_search(self):
        resp = self.client.get("/en-US/systems/list_all_systems_ajax/?_=1326317772224&sEcho=4&iColumns=8&sColumns=&iDisplayStart=0&iDisplayLength=10&mDataProp_0=0&mDataProp_1=1&mDataProp_2=2&mDataProp_3=3&mDataProp_4=4&mDataProp_5=5&mDataProp_6=6&mDataProp_7=7&sSearch=fake-hostname2&bRegex=false&sSearch_0=&bRegex_0=false&bSearchable_0=true&sSearch_1=&bRegex_1=false&bSearchable_1=true&sSearch_2=&bRegex_2=false&bSearchable_2=true&sSearch_3=&bRegex_3=false&bSearchable_3=true&sSearch_4=&bRegex_4=false&bSearchable_4=true&sSearch_5=&bRegex_5=false&bSearchable_5=true&sSearch_6=&bRegex_6=false&bSearchable_6=true&sSearch_7=&bRegex_7=false&bSearchable_7=true&iSortingCols=1&iSortCol_0=0&sSortDir_0=asc&bSortable_0=true&bSortable_1=true&bSortable_2=true&bSortable_3=true&bSortable_4=true&bSortable_5=true&bSortable_6=true&bSortable_7=false", follow=True)
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content)
        obj = obj['aaData']
        self.assertEqual(len(obj),1)
        self.assertEqual(obj[0][0], '1,fake-hostname2')

    def test_failed_search(self):
        resp = self.client.get("/en-US/systems/list_all_systems_ajax/?_=1326317772224&sEcho=4&iColumns=8&sColumns=&iDisplayStart=0&iDisplayLength=10&mDataProp_0=0&mDataProp_1=1&mDataProp_2=2&mDataProp_3=3&mDataProp_4=4&mDataProp_5=5&mDataProp_6=6&mDataProp_7=7&sSearch=asdfasdfasdf&bRegex=false&sSearch_0=&bRegex_0=false&bSearchable_0=true&sSearch_1=&bRegex_1=false&bSearchable_1=true&sSearch_2=&bRegex_2=false&bSearchable_2=true&sSearch_3=&bRegex_3=false&bSearchable_3=true&sSearch_4=&bRegex_4=false&bSearchable_4=true&sSearch_5=&bRegex_5=false&bSearchable_5=true&sSearch_6=&bRegex_6=false&bSearchable_6=true&sSearch_7=&bRegex_7=false&bSearchable_7=true&iSortingCols=1&iSortCol_0=0&sSortDir_0=asc&bSortable_0=true&bSortable_1=true&bSortable_2=true&bSortable_3=true&bSortable_4=true&bSortable_5=true&bSortable_6=true&bSortable_7=false", follow=True)
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content)
        obj = obj['aaData']
        self.assertEqual(len(obj),0)

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
        self.assertEqual(True,system.check_for_adapter(1))
        self.assertEqual(False,system.check_for_adapter(3))

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
        resp = self.client.post("/en-US/systems/quicksearch/", {'quicksearch':'fake-hostname2', 'is_test':'True'}, follow=True)
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content)
        self.assertEqual(1,obj[0]['pk'])
        self.assertEqual('fake-hostname2',obj[0]['fields']['hostname'])

    def test_quicksearch_by_asset_tag(self):
        resp = self.client.post("/en-US/systems/quicksearch/", {'quicksearch':'65432', 'is_test':'True'})
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content)
        self.assertEqual(1,obj[0]['pk'])
        self.assertEqual('fake-hostname2',obj[0]['fields']['hostname'])

