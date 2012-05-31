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
from mdns.utils import _str_increment_soa

ex_tx1 = """
$TTL 3600
@       IN  SOA ns.mozilla.org. sysadmins.mozilla.org.(
            2012051500
            10800
            3600
            604800
            1800
            )
        IN  NS  ns.mozilla.org.

$GENERATE 0-255 $     IN PTR  unused-10-8-2-$.console.phx1.mozilla.com.
"""
ex_tx1_inc = """
$TTL 3600
@       IN  SOA ns.mozilla.org. sysadmins.mozilla.org.(
            2012051501
            10800
            3600
            604800
            1800
            )
        IN  NS  ns.mozilla.org.

$GENERATE 0-255 $     IN PTR  unused-10-8-2-$.console.phx1.mozilla.com.
"""
ex_tx2 = """
$TTL 300

@                           IN  SOA ns.mozilla.org. noc.mozilla.com.  (
                                2012051500 ; Foobar
                                10800
                                3600
                                604800
                                1800
                            )

                            IN  NS      ns1.mozilla.org.
                            IN  NS      ns2.mozilla.org.
                            IN  NS      ns3.mozilla.org.

                            IN  MX 10   mx1.corp.phx1.mozilla.com.
                            IN  MX 10   mx2.corp.phx1.mozilla.com.

1 IN PTR v85.fw1.bugs.scl3.mozilla.net.

20  IN  PTR db1.stage.bugs.scl3.mozilla.com.
21  IN  PTR web1.stage.bugs.scl3.mozilla.com.
22  IN  PTR web2.stage.bugs.scl3.mozilla.com.
23  IN  PTR db2.stage.bugs.scl3.mozilla.com
"""
ex_tx2_inc = """
$TTL 300

@                           IN  SOA ns.mozilla.org. noc.mozilla.com.  (
                                2012051501 ; Foobar
                                10800
                                3600
                                604800
                                1800
                            )

                            IN  NS      ns1.mozilla.org.
                            IN  NS      ns2.mozilla.org.
                            IN  NS      ns3.mozilla.org.

                            IN  MX 10   mx1.corp.phx1.mozilla.com.
                            IN  MX 10   mx2.corp.phx1.mozilla.com.

1 IN PTR v85.fw1.bugs.scl3.mozilla.net.

20  IN  PTR db1.stage.bugs.scl3.mozilla.com.
21  IN  PTR web1.stage.bugs.scl3.mozilla.com.
22  IN  PTR web2.stage.bugs.scl3.mozilla.com.
23  IN  PTR db2.stage.bugs.scl3.mozilla.com
"""
ex_tx3 = """
$TTL 300

foo.bar                           IN  SOA ns.mozilla.org. noc.mozilla.com.  (
                                2012052900
                                10800
                                3600
                                604800
                                1800
                            )

                            IN  NS      ns1.mozilla.org.
                            IN  NS      ns2.mozilla.org.
                            IN  NS      ns3.mozilla.org.

                            IN  MX 10   mx1.corp.phx1.mozilla.com.
                            IN  MX 10   mx2.corp.phx1.mozilla.com.

; glue records for the MX entries since they're a subdomain of this zone but not in this zone
mx1.corp.phx1.mozilla.com. 60 IN A 63.245.216.69
mx2.corp.phx1.mozilla.com. 60 IN A 63.245.216.7
"""
ex_tx3_inc = """
$TTL 300

foo.bar                           IN  SOA ns.mozilla.org. noc.mozilla.com.  (
                                2012052901
                                10800
                                3600
                                604800
                                1800
                            )

                            IN  NS      ns1.mozilla.org.
                            IN  NS      ns2.mozilla.org.
                            IN  NS      ns3.mozilla.org.

                            IN  MX 10   mx1.corp.phx1.mozilla.com.
                            IN  MX 10   mx2.corp.phx1.mozilla.com.

; glue records for the MX entries since they're a subdomain of this zone but not in this zone
mx1.corp.phx1.mozilla.com. 60 IN A 63.245.216.69
mx2.corp.phx1.mozilla.com. 60 IN A 63.245.216.7
"""

ex_tx4 = """
$TTL 300
$TTL 800
$ORIGIN foo

@                           IN  SOA ns.mozilla.org. noc.mozilla.com.  (
                                2012051701
                                10800
                                3600
                                604800
                                1800
                            )

                            IN  NS      ns1.mozilla.org.
                            IN  NS      ns2.mozilla.org.
                            IN  NS      ns3.mozilla.org.

                            IN  MX 10   mx1.corp.phx1.mozilla.com.
                            IN  MX 10   mx2.corp.phx1.mozilla.com.

1   IN PTR v111.fw1.labs.scl3.mozilla.net.
41  IN PTR vm1.phy.labs.scl3.mozilla.com.
41  IN PTR vm1-5.phy.labs.scl3.mozilla.com.
42  IN PTR vm1-6.phy.labs.scl3.mozilla.com.
43  IN PTR vm1-7.phy.labs.scl3.mozilla.com.
44  IN PTR vm1-8.phy.labs.scl3.mozilla.com.
45  IN PTR vm1-1.phy.labs.scl3.mozilla.com.
"""
ex_tx4_inc = """
$TTL 300
$TTL 800
$ORIGIN foo

@                           IN  SOA ns.mozilla.org. noc.mozilla.com.  (
                                2012051702
                                10800
                                3600
                                604800
                                1800
                            )

                            IN  NS      ns1.mozilla.org.
                            IN  NS      ns2.mozilla.org.
                            IN  NS      ns3.mozilla.org.

                            IN  MX 10   mx1.corp.phx1.mozilla.com.
                            IN  MX 10   mx2.corp.phx1.mozilla.com.

1   IN PTR v111.fw1.labs.scl3.mozilla.net.
41  IN PTR vm1.phy.labs.scl3.mozilla.com.
41  IN PTR vm1-5.phy.labs.scl3.mozilla.com.
42  IN PTR vm1-6.phy.labs.scl3.mozilla.com.
43  IN PTR vm1-7.phy.labs.scl3.mozilla.com.
44  IN PTR vm1-8.phy.labs.scl3.mozilla.com.
45  IN PTR vm1-1.phy.labs.scl3.mozilla.com.
"""

ex_tx5 = """
$TTL 300
$TTL 800
$ORIGIN foo

@                           IN  SOA ns.mozilla.org. noc.mozilla.com.  2012051701 10800 3600 604800 1800
                            IN  NS      ns1.mozilla.org.
                            IN  NS      ns2.mozilla.org.
"""
ex_tx5_inc = """
$TTL 300
$TTL 800
$ORIGIN foo

@                           IN  SOA ns.mozilla.org. noc.mozilla.com.  2012051702 10800 3600 604800 1800
                            IN  NS      ns1.mozilla.org.
                            IN  NS      ns2.mozilla.org.
"""

ex_tx6 = """
$TTL 300
$TTL 800
$ORIGIN foo

@                           IN  SOA ns.mozilla.org. noc.mozilla.com.  (2012051701 10800 3600 604800 1800)
                            IN  NS      ns1.mozilla.org.
                            IN  NS      ns2.mozilla.org.
"""
ex_tx6_inc = """
$TTL 300
$TTL 800
$ORIGIN foo

@                           IN  SOA ns.mozilla.org. noc.mozilla.com.  (2012051702 10800 3600 604800 1800)
                            IN  NS      ns1.mozilla.org.
                            IN  NS      ns2.mozilla.org.
"""

ex_tx7 = """
$TTL 300
$TTL 800
$ORIGIN foo

@                           IN  SOA ns.mozilla.org. noc.mozilla.com.  ( 2012051701 10800 3600 604800 1800 )
                            IN  NS      ns1.mozilla.org.
                            IN  NS      ns2.mozilla.org.
"""
ex_tx7_inc = """
$TTL 300
$TTL 800
$ORIGIN foo

@                           IN  SOA ns.mozilla.org. noc.mozilla.com.  ( 2012051702 10800 3600 604800 1800 )
                            IN  NS      ns1.mozilla.org.
                            IN  NS      ns2.mozilla.org.
"""

from StringIO import StringIO
import pdb

class SOAParseTests(TestCase):

    def test_parse_1(self):
        ios = StringIO(ex_tx1)
        res = _str_increment_soa(ios)
        self.assertEqual(ex_tx1_inc, res)

    def test_parse_2(self):
        ios = StringIO(ex_tx2)
        res = _str_increment_soa(ios)
        self.assertEqual(ex_tx2_inc, res)

    def test_parse_3(self):
        ios = StringIO(ex_tx3)
        res = _str_increment_soa(ios)
        self.assertEqual(ex_tx3_inc, res)

    def test_parse_4(self):
        ios = StringIO(ex_tx4)
        res = _str_increment_soa(ios)
        self.assertEqual(ex_tx4_inc, res)

    def test_parse_5(self):
        ios = StringIO(ex_tx5)
        res = _str_increment_soa(ios)
        self.assertEqual(ex_tx5_inc, res)

    def test_parse_6(self):
        ios = StringIO(ex_tx6)
        res = _str_increment_soa(ios)
        self.assertEqual(ex_tx6_inc, res)

    def test_parse_7(self):
        ios = StringIO(ex_tx7)
        res = _str_increment_soa(ios)
        self.assertEqual(ex_tx7_inc, res)

