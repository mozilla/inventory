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
asf.asdf IN A 10.0.0.1
"""

ex_txt1 = """
foo bar
$INCLUDE foo/bar/private

$INCLUDE foo/bar/inventory ; This include preserves $ORIGIN

asf.asdf IN A 10.0.0.1
"""

txt2 = """
; BE SURE TO INCREMENT THE SERIAL IN:
; zones/mozilla.com/scl3/SOA

$INCLUDE zones/mozilla.com/scl3/public
$INCLUDE zones/mozilla.com/scl3/releng

$ORIGIN scl3.mozilla.com.

$ORIGIN console.scl3.mozilla.com.
conserver1.r101-3   IN  A   10.22.0.10
conserver1.r101-8   IN  A   10.22.0.11
conserver1.r101-11  IN  A   10.22.0.12
conserver1.r101-16  IN  A   10.22.0.13
conserver1.r101-21  IN  A   10.22.0.14
conserver1.r102-3   IN  A   10.22.0.15
conserver1.r102-8   IN  A   10.22.0.16
"""

ex_txt2 = """
; BE SURE TO INCREMENT THE SERIAL IN:
; zones/mozilla.com/scl3/SOA

$INCLUDE zones/mozilla.com/scl3/public
$INCLUDE zones/mozilla.com/scl3/releng

$ORIGIN scl3.mozilla.com.

$ORIGIN console.scl3.mozilla.com.

$INCLUDE foo/bar/inventory ; This include preserves $ORIGIN

conserver1.r101-3   IN  A   10.22.0.10
conserver1.r101-8   IN  A   10.22.0.11
conserver1.r101-11  IN  A   10.22.0.12
conserver1.r101-16  IN  A   10.22.0.13
conserver1.r101-21  IN  A   10.22.0.14
conserver1.r102-3   IN  A   10.22.0.15
conserver1.r102-8   IN  A   10.22.0.16
"""

txt3 = """
; BE SURE TO INCREMENT THE SERIAL IN:
; zones/mozilla.com/phx1/SOA

$INCLUDE zones/mozilla.com/phx1/public

$ORIGIN phx1.mozilla.com.
tp-socorro01-master01   IN A       10.8.70.100
tp-socorro01-master02   IN A       10.8.70.101
tp-socorro01-rw-zeus    IN A       10.8.70.109
tp-socorro01-ro-zeus    IN A       10.8.70.134
db-internal-rw-zeus     IN A       10.8.70.240
db-internal-ro-zeus     IN A       10.8.70.249
db-engagement-rw-zeus   IN A       10.8.70.230
db-engagement-ro-zeus   IN A       10.8.70.239
db-engagement-dev-rw    IN A       10.8.70.237
db-engagement-dev-ro    IN A       10.8.70.238
receipt-sign1.dev       IN A       10.8.83.35
sp-admin01      IN A        10.8.75.29

sysadmin1.sandbox   IN A        10.8.76.10
inventory-dev       IN CNAME    sysadmin1.sandbox 
inventory           IN A        10.8.81.14 
ldap-dev        IN CNAME    sysadmin1.sandbox 
rhel6dev64.sandbox  IN A        10.8.76.11
dnssec-test     IN A    10.8.76.12

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

tp-socorro01-master01   IN A       10.8.70.100
tp-socorro01-master02   IN A       10.8.70.101
tp-socorro01-rw-zeus    IN A       10.8.70.109
tp-socorro01-ro-zeus    IN A       10.8.70.134
db-internal-rw-zeus     IN A       10.8.70.240
db-internal-ro-zeus     IN A       10.8.70.249
db-engagement-rw-zeus   IN A       10.8.70.230
db-engagement-ro-zeus   IN A       10.8.70.239
db-engagement-dev-rw    IN A       10.8.70.237
db-engagement-dev-ro    IN A       10.8.70.238
receipt-sign1.dev       IN A       10.8.83.35
sp-admin01      IN A        10.8.75.29

sysadmin1.sandbox   IN A        10.8.76.10
inventory-dev       IN CNAME    sysadmin1.sandbox 
inventory           IN A        10.8.81.14 
ldap-dev        IN CNAME    sysadmin1.sandbox 
rhel6dev64.sandbox  IN A        10.8.76.11
dnssec-test     IN A    10.8.76.12

puppet                  IN CNAME dp-nagios01.phx.mozilla.com.
scalarcmgmt         IN  CNAME   scalarc1.db.phx1.mozilla.com.
scalarcmgmt2        IN  CNAME   scalarc2.db.phx1.mozilla.com.
"""

txt4 = """
;BE SURE TO INCREMENT THE SERIAL IN:
; zones/mozilla.com/tor1/SOA

aruba-master    IN  A       10.242.0.20
crashplan   IN  CNAME       backup1.private.tor1.mozilla.com.
caadm01     IN  A       10.242.40.11
"""

ex_txt4 = """
;BE SURE TO INCREMENT THE SERIAL IN:
; zones/mozilla.com/tor1/SOA


$INCLUDE foo/bar/inventory ; This include preserves $ORIGIN

aruba-master    IN  A       10.242.0.20
crashplan   IN  CNAME       backup1.private.tor1.mozilla.com.
caadm01     IN  A       10.242.40.11
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
wifi1      IN  A       10.242.0.20
wifi1a     IN  A       10.242.0.21
wifi1b     IN  A       10.242.0.22

$ORIGIN private.tor1.mozilla.com.

infosec1    IN  A       10.240.2.10

fw1         IN  A   10.242.75.1
admin1      IN  A   10.242.75.5
admin1a     IN  A       10.242.75.6
admin1b     IN  A       10.242.75.7
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

wifi1      IN  A       10.242.0.20
wifi1a     IN  A       10.242.0.21
wifi1b     IN  A       10.242.0.22

$ORIGIN private.tor1.mozilla.com.

infosec1    IN  A       10.240.2.10

fw1         IN  A   10.242.75.1
admin1      IN  A   10.242.75.5
admin1a     IN  A       10.242.75.6
admin1b     IN  A       10.242.75.7
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
wifi1      IN  A       10.242.0.20
wifi1a     IN  A       10.242.0.21
wifi1b     IN  A       10.242.0.22

$ORIGIN private.tor1.mozilla.com.

infosec1    IN  A       10.240.2.10

fw1         IN  A   10.242.75.1
admin1      IN  A   10.242.75.5
admin1a     IN  A       10.242.75.6
admin1b     IN  A       10.242.75.7
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

wifi1      IN  A       10.242.0.20
wifi1a     IN  A       10.242.0.21
wifi1b     IN  A       10.242.0.22

$ORIGIN private.tor1.mozilla.com.

infosec1    IN  A       10.240.2.10

fw1         IN  A   10.242.75.1
admin1      IN  A   10.242.75.5
admin1a     IN  A       10.242.75.6
admin1b     IN  A       10.242.75.7
"""

txt7 = """
;BE SURE TO INCREMENT THE SERIAL IN:
; zones/mozilla.com/tor1/SOA

$INCLUDE zones/mozilla.com/tor1/public

$INCLUDE foo/bar/inventory ; This include preserves $ORIGIN

wifi1      IN  A       10.242.0.20
"""

ex_txt7 = """
;BE SURE TO INCREMENT THE SERIAL IN:
; zones/mozilla.com/tor1/SOA

$INCLUDE zones/mozilla.com/tor1/public

$INCLUDE foo/bar/inventory ; This include preserves $ORIGIN

wifi1      IN  A       10.242.0.20
"""

txt8 = """
$INCLUDE foo/bar/inventory ; This include preserves $ORIGIN
"""

ex_txt8 = """
$INCLUDE foo/bar/inventory ; This include preserves $ORIGIN
"""

class EnsureIncludeTests(TestCase):

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
        res = fun(ios, 'forward', include_file)
        self.assertEqual(res, expect)
