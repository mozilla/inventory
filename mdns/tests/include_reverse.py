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
from systems.models import KeyValue, System
from StringIO import StringIO
from mdns.utils import _ensure_include
import pdb

txt1 = """
foo bar
$INCLUDE foo/bar/private
10.0.0.1 IN PTR  asf.asdf
"""

ex_txt1 = """
foo bar
$INCLUDE foo/bar/private

$INCLUDE foo/bar/inventory ; This include preserves $ORIGIN

10.0.0.1 IN PTR  asf.asdf
"""

txt2 = """
; BE SURE TO INCREMENT THE SERIAL IN:
; zones/mozilla.com/scl3/SOA

$INCLUDE zones/mozilla.com/scl3/public
$INCLUDE zones/mozilla.com/scl3/releng

$ORIGIN scl3.mozilla.com.

$ORIGIN console.scl3.mozilla.com.
10.22.0.10 IN  PTR    conserver1.r101-3
10.22.0.11 IN  PTR    conserver1.r101-8
10.22.0.12 IN  PTR    conserver1.r101-11
10.22.0.13 IN  PTR    conserver1.r101-16
10.22.0.14 IN  PTR    conserver1.r101-21
10.22.0.15 IN  PTR    conserver1.r102-3
10.22.0.16 IN  PTR    conserver1.r102-8
"""

ex_txt2 = """
; BE SURE TO INCREMENT THE SERIAL IN:
; zones/mozilla.com/scl3/SOA

$INCLUDE zones/mozilla.com/scl3/public
$INCLUDE zones/mozilla.com/scl3/releng

$ORIGIN scl3.mozilla.com.

$ORIGIN console.scl3.mozilla.com.

$INCLUDE foo/bar/inventory ; This include preserves $ORIGIN

10.22.0.10 IN  PTR    conserver1.r101-3
10.22.0.11 IN  PTR    conserver1.r101-8
10.22.0.12 IN  PTR    conserver1.r101-11
10.22.0.13 IN  PTR    conserver1.r101-16
10.22.0.14 IN  PTR    conserver1.r101-21
10.22.0.15 IN  PTR    conserver1.r102-3
10.22.0.16 IN  PTR    conserver1.r102-8
"""

txt3 = """
; BE SURE TO INCREMENT THE SERIAL IN:
; zones/mozilla.com/phx1/SOA

$INCLUDE zones/mozilla.com/phx1/public

$ORIGIN phx1.mozilla.com.
10.8.70.100 IN PTR       tp-socorro01-master01
10.8.70.101 IN PTR       tp-socorro01-master02
10.8.70.109 IN PTR       tp-socorro01-rw-zeus
10.8.70.134 IN PTR       tp-socorro01-ro-zeus
10.8.70.240 IN PTR       db-internal-rw-zeus
10.8.70.249 IN PTR       db-internal-ro-zeus
10.8.70.230 IN PTR       db-engagement-rw-zeus
10.8.70.239 IN PTR       db-engagement-ro-zeus
10.8.70.237 IN PTR       db-engagement-dev-rw
10.8.70.238 IN PTR       db-engagement-dev-ro
10.8.83.35 IN PTR       receipt-sign1.dev
10.8.75.29 IN PTR        sp-admin01

10.8.76.10 IN PTR        sysadmin1.sandbox
inventory-dev       IN CNAME    sysadmin1.sandbox
10.8.81.14  IN PTR        inventory
ldap-dev        IN CNAME    sysadmin1.sandbox
10.8.76.11 IN PTR        rhel6dev64.sandbox

10.8.76.12 IN PTR    dnssec-test

puppet                  IN CNAME dp-nagios01.phx.mozilla.com.
scalarcmgmt         IN  CNAME   scalarc1.db.phx1.mozilla.com.
scalarcmgmt2        IN  CNAME   scalarc2.db.phx1.mozilla.com.
"""

ex_txt3 = """
; BE SURE TO INCREMENT THE SERIAL IN:
; zones/mozilla.com/phx1/SOA

$INCLUDE zones/mozilla.com/phx1/public

$ORIGIN phx1.mozilla.com.

$INCLUDE foo/bar/inventory ; This include preserves $ORIGIN

10.8.70.100 IN PTR       tp-socorro01-master01
10.8.70.101 IN PTR       tp-socorro01-master02
10.8.70.109 IN PTR       tp-socorro01-rw-zeus
10.8.70.134 IN PTR       tp-socorro01-ro-zeus
10.8.70.240 IN PTR       db-internal-rw-zeus
10.8.70.249 IN PTR       db-internal-ro-zeus
10.8.70.230 IN PTR       db-engagement-rw-zeus
10.8.70.239 IN PTR       db-engagement-ro-zeus
10.8.70.237 IN PTR       db-engagement-dev-rw
10.8.70.238 IN PTR       db-engagement-dev-ro
10.8.83.35 IN PTR       receipt-sign1.dev
10.8.75.29 IN PTR        sp-admin01

10.8.76.10 IN PTR        sysadmin1.sandbox
inventory-dev       IN CNAME    sysadmin1.sandbox
10.8.81.14  IN PTR        inventory
ldap-dev        IN CNAME    sysadmin1.sandbox
10.8.76.11 IN PTR        rhel6dev64.sandbox

10.8.76.12 IN PTR    dnssec-test

puppet                  IN CNAME dp-nagios01.phx.mozilla.com.
scalarcmgmt         IN  CNAME   scalarc1.db.phx1.mozilla.com.
scalarcmgmt2        IN  CNAME   scalarc2.db.phx1.mozilla.com.
"""

txt4 = """
;BE SURE TO INCREMENT THE SERIAL IN:
; zones/mozilla.com/tor1/SOA

10.242.0.20 IN  PTR       aruba-master
crashplan   IN  CNAME       backup1.private.tor1.mozilla.com.
10.242.40.11 IN  PTR       caadm01
"""

ex_txt4 = """
;BE SURE TO INCREMENT THE SERIAL IN:
; zones/mozilla.com/tor1/SOA


$INCLUDE foo/bar/inventory ; This include preserves $ORIGIN

10.242.0.20 IN  PTR       aruba-master
crashplan   IN  CNAME       backup1.private.tor1.mozilla.com.
10.242.40.11 IN  PTR       caadm01
"""

txt5 = """
;BE SURE TO INCREMENT THE SERIAL IN:
; zones/mozilla.com/tor1/SOA

$INCLUDE zones/mozilla.com/tor1/public

$ORIGIN tor1.mozilla.com.

aruba-master    IN  FOO       10.242.0.20
crashplan   IN  CNAME       backup1.private.tor1.mozilla.com.
caadm01     IN  FOO       10.242.40.11

$ORIGIN ops.tor1.mozilla.com.

fw1         IN  FOO   10.242.0.1

10.242.0.20 IN  PTR       wifi1

10.242.0.21 IN  PTR       wifi1a

10.242.0.22 IN  PTR       wifi1b

$ORIGIN private.tor1.mozilla.com.

10.240.2.10 IN  PTR       infosec1

    
   10.242.75.1  IN  PTR   fw1

10.242.75.5 IN  PTR   admin1

10.242.75.6 IN  PTR       admin1a

10.242.75.7 IN  PTR       admin1b
"""

ex_txt5 = """
;BE SURE TO INCREMENT THE SERIAL IN:
; zones/mozilla.com/tor1/SOA

$INCLUDE zones/mozilla.com/tor1/public

$ORIGIN tor1.mozilla.com.

aruba-master    IN  FOO       10.242.0.20
crashplan   IN  CNAME       backup1.private.tor1.mozilla.com.
caadm01     IN  FOO       10.242.40.11

$ORIGIN ops.tor1.mozilla.com.

fw1         IN  FOO   10.242.0.1


$INCLUDE foo/bar/inventory ; This include preserves $ORIGIN

10.242.0.20 IN  PTR       wifi1

10.242.0.21 IN  PTR       wifi1a

10.242.0.22 IN  PTR       wifi1b

$ORIGIN private.tor1.mozilla.com.

10.240.2.10 IN  PTR       infosec1

    
   10.242.75.1  IN  PTR   fw1

10.242.75.5 IN  PTR   admin1

10.242.75.6 IN  PTR       admin1a

10.242.75.7 IN  PTR       admin1b
"""

txt6 = """
;BE SURE TO INCREMENT THE SERIAL IN:
; zones/mozilla.com/tor1/SOA

$INCLUDE zones/mozilla.com/tor1/public

$ORIGIN tor1.mozilla.com.

            IN  FOO       10.242.0.20
crashplan   IN  CNAME       backup1.private.tor1.mozilla.com.
caadm01     IN  FOO       10.242.40.11

$ORIGIN ops.tor1.mozilla.com.

fw1         IN  FOO   10.242.0.1

10.242.0.20 IN  PTR       wifi1

10.242.0.21 IN  PTR       wifi1a

10.242.0.22 IN  PTR       wifi1b

$ORIGIN private.tor1.mozilla.com.

10.240.2.10 IN  PTR       infosec1

    
   10.242.75.1  IN  PTR   fw1

10.242.75.5 IN  PTR   admin1

10.242.75.6 IN  PTR       admin1a

10.242.75.7 IN  PTR       admin1b
"""

ex_txt6 = """
;BE SURE TO INCREMENT THE SERIAL IN:
; zones/mozilla.com/tor1/SOA

$INCLUDE zones/mozilla.com/tor1/public

$ORIGIN tor1.mozilla.com.

            IN  FOO       10.242.0.20
crashplan   IN  CNAME       backup1.private.tor1.mozilla.com.
caadm01     IN  FOO       10.242.40.11

$ORIGIN ops.tor1.mozilla.com.

fw1         IN  FOO   10.242.0.1


$INCLUDE foo/bar/inventory ; This include preserves $ORIGIN

10.242.0.20 IN  PTR       wifi1

10.242.0.21 IN  PTR       wifi1a

10.242.0.22 IN  PTR       wifi1b

$ORIGIN private.tor1.mozilla.com.

10.240.2.10 IN  PTR       infosec1

    
   10.242.75.1  IN  PTR   fw1

10.242.75.5 IN  PTR   admin1

10.242.75.6 IN  PTR       admin1a

10.242.75.7 IN  PTR       admin1b
"""

txt7 = """
;BE SURE TO INCREMENT THE SERIAL IN:
; zones/mozilla.com/tor1/SOA

$INCLUDE zones/mozilla.com/tor1/public

$INCLUDE foo/bar/inventory ; This include preserves $ORIGIN


10.242.0.20 IN  PTR       wifi1
"""

ex_txt7 = """
;BE SURE TO INCREMENT THE SERIAL IN:
; zones/mozilla.com/tor1/SOA

$INCLUDE zones/mozilla.com/tor1/public

$INCLUDE foo/bar/inventory ; This include preserves $ORIGIN


10.242.0.20 IN  PTR       wifi1
"""

txt8 = """
$INCLUDE foo/bar/inventory ; This include preserves $ORIGIN
"""

ex_txt8 = """
$INCLUDE foo/bar/inventory ; This include preserves $ORIGIN
"""

class EnsureRevIncludeTests(TestCase):

    def test_1(self):
        self._do_test(txt1, ex_txt1, _ensure_include, include_file='foo/bar/inventory')
    def test_2(self):
        self._do_test(txt2, ex_txt2, _ensure_include, include_file='foo/bar/inventory')
    def test_3(self):
        self._do_test(txt3, ex_txt3, _ensure_include, include_file='foo/bar/inventory')
    def test_4(self):
        self._do_test(txt4, ex_txt4, _ensure_include, include_file='foo/bar/inventory')
    def test_5(self):
        self._do_test(txt5, ex_txt5, _ensure_include, include_file='foo/bar/inventory')
    def test_6(self):
        self._do_test(txt6, ex_txt6, _ensure_include, include_file='foo/bar/inventory')
    def test_7(self):
        self._do_test(txt7, ex_txt7, _ensure_include, include_file='foo/bar/inventory')
    def test_8(self):
        self._do_test(txt8, ex_txt8, _ensure_include, include_file='foo/bar/inventory')


    def _do_test(self, text, expect, fun, include_file):
        ios = StringIO(text)
        res = fun(ios, 'reverse', include_file)
        self.assertEqual(res, expect)
