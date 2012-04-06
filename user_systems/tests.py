"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""
import sys
import sys
import os
_base = os.path.dirname(__file__)
site_root = os.path.realpath(os.path.join(_base, '../'))
sys.path.append(site_root)
import manage
from django.test import TestCase
import models

from test_utils import setup_test_environment,TestCase
setup_test_environment()
from django.contrib.auth.models import User
from django.test.client import Client

class OwnerTest(TestCase):
    fixtures = ['user_systems_test_data']
    def setUp(self):
        self.client = Client()
    def test_owner_list(self):
        resp = self.client.get('/user_systems/owners/', follow=True)
        print User.objects.all()
        self.assertEqual(resp.status_code,200)
        print resp.context[0]['owner_list']
        self.assertTrue(len(resp.context[0]['owner_list']) > 0)
    def test_owner_show(self):
        resp = self.client.get('/user_systems/owners/show/1/', follow=True)
        self.assertEqual(resp.status_code,200)
        print resp.context[0]['owner_list']
        self.assertTrue(len(resp.context[0]['owner_list']) > 0)
