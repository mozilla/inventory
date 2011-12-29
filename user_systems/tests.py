"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from django.test import TestCase

from django.test.client import Client

class OwnerTest(TestCase):
    def setUp(self):
        self.client = Client()
    def test_owner_list(self):
        resp = self.client.get('/user_systems/owners/', follow=True)
        self.assertEqual(resp.status_code,200)
        print resp.context[0]['owner_list']
        self.assertTrue(len(resp.context[0]['owner_list']) > 0)
    def test_owner_show(self):
        resp = self.client.get('/user_systems/owners/show/1/', follow=True)
        self.assertEqual(resp.status_code,200)
        print resp.context[0]['owner_list']
        self.assertTrue(len(resp.context[0]['owner_list']) > 0)
