"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""
from models import Truth, KeyValue
from django.test import TestCase
from django.test.client import Client

class TruthTest(TestCase):
    fixtures = ['testdata.json']

    def setUp(self):
        self.client = Client()
        self.key_name = 'New Test Key Name'
        self.key_description = 'New Test Description'
        self.new_key_name = 'Updated New Test Key Name'
        self.new_key_description = 'Updated New Test Description'

    def test_index(self):
        resp = self.client.get('/truth/', follow=True)
        self.assertEqual(200, resp.status_code)

    def test_create(self):

        resp = self.client.get('/truth/create/', follow=True)
        self.assertEqual(200, resp.status_code)
        resp = self.client.post('/en-US/truth/create/', {'name':self.key_name, 'description':self.key_description}, follow=True)
        self.assertEqual(200, resp.status_code)
        kv = Truth.objects.get(name=self.key_name)
        self.assertEqual(kv.name, self.key_name)
        self.assertEqual(kv.description, self.key_description)

    def test_update(self):
        update_url = '/en-US/truth/edit/1/'
        resp = self.client.post(update_url, {'name':self.new_key_name, 'description':self.new_key_description}, follow=True)
        self.assertEqual(200, resp.status_code)
        kv = Truth.objects.get(id=1)
        self.assertEqual(kv.name, self.new_key_name)
        self.assertEqual(kv.description, self.new_key_description)

    def test_delete(self):
        resp = self.client.post('/en-US/truth/delete/1/', follow=True)
        self.assertEqual(200, resp.status_code)
        resp = self.client.get('/truth/create/1/', {'name':self.key_name, 'description':self.key_description}, follow=True)
        self.assertEqual(404, resp.status_code)
        try:
            kv = Truth.objects.get(id=1)
        except:
            kv = None
        self.assertEqual(None, kv)
