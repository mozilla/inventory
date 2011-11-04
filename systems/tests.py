#!/usr/bin/python
"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from django.test import TestCase
from django.test.client import Client
from models import KeyValue, System
try:
    import json
except:
    from django.utils import simplejson as json

from inventory.systems import models

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
        resp = self.client.post("/systems/quicksearch/", {'quicksearch':'natasha', 'is_test':'True'})
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content)
        self.assertEqual(1,obj[0]['pk'])
        self.assertEqual('natasha',obj[0]['fields']['hostname'])

    def test_quicksearch_by_asset_tag(self):
        resp = self.client.post("/systems/quicksearch/", {'quicksearch':'65432', 'is_test':'True'})
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content)
        self.assertEqual(1,obj[0]['pk'])
        self.assertEqual('natasha',obj[0]['fields']['hostname'])

