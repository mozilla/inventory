"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""
import sys
import os
_base = os.path.dirname(__file__)
site_root = os.path.realpath(os.path.join(_base, '../'))
sys.path.append(site_root)
from django.test import TestCase

from django.contrib.auth.models import User
from django.test.client import Client
from test_utils import setup_test_environment,TestCase
setup_test_environment()
from test_utils import RequestFactory
from systems import models
class OncallTest(TestCase):
    fixtures = ['user_systems_test_data.json']
    def setUp(self):
        self.client = Client()
        self.rf = RequestFactory()

    def test_initial(self):
        u1 = User.objects.get(username='user1@domain.com')
        self.assertEqual(u1.username,'user1@domain.com')
        self.assertEqual(u1.get_profile().is_desktop_oncall, True)
        self.assertEqual(u1.get_profile().is_sysadmin_oncall, True)

    def test_desktop_oncall_count(self):
        oncalls = User.objects.select_related().filter(userprofile__is_desktop_oncall=1)
        self.assertEqual(len(oncalls), 3)

    def test_sysadmin_oncall_count(self):
        oncalls = User.objects.select_related().filter(userprofile__is_sysadmin_oncall=1)
        self.assertEqual(len(oncalls), 3)

    def test_oncall_index_page(self):
        resp = self.client.get('/systems/oncall/', follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context['form'].desktop_support_choices), 3)
        self.assertEqual(len(resp.context['form'].sysadmin_support_choices), 3)
        self.assertEqual(resp.context['current_desktop_oncall'], 'user1@domain.com')
        self.assertEqual(resp.context['current_sysadmin_oncall'], 'user2@domain.com')

    def test_updating_sysadmin_oncall(self):
        rpost = self.client.post('/en-US/systems/oncall/', {'submit':'Save', 'sysadmin_support':'user1@domain.com', 'desktop_support':'user2@domain.com'},follow=False)
        self.assertEqual(rpost.status_code, 200)
        resp = self.client.get('/systems/oncall/', follow=True)
        self.assertEqual(resp.context['current_desktop_oncall'], 'user1@domain.com')
        self.assertEqual(resp.context['current_sysadmin_oncall'], 'user2@domain.com')

    def test_updating_desktop_oncall(self):
        rpost = self.client.post('/en-US/systems/oncall/', {'submit':'Save', 'sysadmin_support':'user1@domain.com', 'desktop_support':'user1@domain.com'},follow=False)
        self.assertEqual(rpost.status_code, 200)
        resp = self.client.get('/systems/oncall/', follow=True)
        self.assertEqual(resp.context['current_desktop_oncall'], 'user1@domain.com')
        self.assertEqual(resp.context['current_sysadmin_oncall'], 'user2@domain.com')

    def test_oncall_timestamp_autocreate(self):
        ret = models.OncallTimestamp.objects.filter(oncall_type='desktop_support')
        import pdb; pdb.set_trace()
        self.assertNotEqual(ret, None)


