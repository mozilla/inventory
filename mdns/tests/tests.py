#!/usr/bin/python
"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

import sys
import os
import manage
from django.test import TestCase
from django.test.client import Client
from system.models import KeyValue, System

def InterFaceTests(TestCase):
    def setUp(self):
        self.s = System()
    def test_get_kv(self):

