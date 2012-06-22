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

def Generate(TestCase):

    def test1(self):
        raw = 'phx-sync544{0,3,d}.services.mozilla.com'
        expect = ['phx-sync544{0,3,d}.services.mozilla.com',
                'phx-sync544{0,3,d}.services.mozilla.com',
                'phx-sync544{0,3,d}.services.mozilla.com']



        res = resolve_generate(raw)
