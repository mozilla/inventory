#!/usr/bin/python
"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from django.test import TestCase
from django.test.client import Client
import manage
try:
    import json
except:
    from django.utils import simplejson as json

from test_utils import setup_test_environment,TestCase
setup_test_environment()
from libs.Rack import Rack
class RackTest(TestCase):
    fixtures = ['testdata.json']
    def setUp(self):
        self.client = Client()

    def tearDown(self):
        self.client = Client()

    def test_constructor(self):
        r = Rack('scl3-101')
        self.assertEquals(r.rack_name, 'scl3-101')

    def test_constructor(self):
        r = Rack('scl3-101')
        self.assertEquals(r.rack_name, 'scl3-101')

    def test_ru(self):
        r = Rack('scl3-101')
        self.assertEquals(int(r.ru), 42)

    def test_width(self):
        r = Rack('scl3-101')
        self.assertEquals(int(r.width), 30)

    def test_system_count(self):
        r = Rack('scl3-101')
        self.assertEquals(len(r.system_list), 2)

    def test_system_count(self):
        r = Rack('scl3-101')
        self.assertEquals(r.systems[0]['system_name'], 'fake-hostname1')
        self.assertEquals(r.systems[1]['system_name'], 'fake-hostname2')

    def test_system_ru(self):
        r = Rack('scl3-101')
        self.assertEquals(int(r.systems[0]['system_ru']), 4)
        self.assertEquals(int(r.systems[1]['system_ru']), 1)

    def test_system_id(self):
        r = Rack('scl3-101')
        self.assertEquals(int(r.systems[1]['system_id']), 1)
        self.assertEquals(int(r.systems[0]['system_id']), 2)

    def test_system_image(self):
        r = Rack('scl3-101')
        self.assertEquals(r.systems[0]['system_image'], None)
        self.assertEquals(r.systems[1]['system_image'], 'hp-1RU.png')

    def test_system_slot(self):
        r = Rack('scl3-101')
        self.assertEquals(int(r.systems[0]['system_slot']), 1)
        self.assertEquals(int(r.systems[1]['system_slot']), 3)

    def test_ethernet_patch_panels(self):
        r = Rack('scl3-101')
        self.assertEquals(len(r.ethernet_patch_panel_24), 1)
        self.assertEquals(len(r.ethernet_patch_panel_48), 2)
        self.assertEquals(int(r.ethernet_patch_panel_24[0]), 42)
        self.assertEquals(int(r.ethernet_patch_panel_48[0]), 40)
        self.assertEquals(int(r.ethernet_patch_panel_48[1]), 38)

    def test_operating_system(self):
        r = Rack('scl3-101')
        self.assertEquals(r.systems[0]['operating_system'], 'RHEL - 6.0')

    def test_server_model(self):
        r = Rack('scl3-101')
        self.assertEquals(r.systems[0]['server_model'], 'HP - DL360')

    def test_oob_ip(self):
        r = Rack('scl3-101')
        self.assertEquals(r.systems[0]['oob_ip'], '192.168.1.11')
