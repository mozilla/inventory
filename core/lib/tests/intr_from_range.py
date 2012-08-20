from django.test import TestCase
from django.core.exceptions import ValidationError

from core.vlan.models import Vlan
from core.site.models import Site
from core.range.models import Range
from core.network.models import Network
from core.interface.static_intr.models import StaticInterface
from core.lib.utils import *

from mozdns.domain.models import Domain
from mozdns.soa.models import SOA

from systems.models import System

import random
import ipaddr
import pdb

class LibTestsRange(TestCase):
    def setUp(self):
        self.system = System()
        Domain.objects.get_or_create(name="com")
        d1, _ = Domain.objects.get_or_create(name="mozilla.com")
        soa, _ = SOA.objects.get_or_create(primary="fo.bar", contact="foo.bar.com",
                comment="foo bar")
        self.s = soa
        d1.soa = soa
        d1.save()

        v, _ = Vlan.objects.get_or_create(name="private", number=3)
        s, _ = Site.objects.get_or_create(name="phx1")
        s1, _ = Site.objects.get_or_create(name="corp", parent = s)
        d, _ = Domain.objects.get_or_create(name="phx1.mozilla.com")
        d.soa = soa
        d.save()
        d1, _ = Domain.objects.get_or_create(name="corp.phx1.mozilla.com")
        d1.soa = soa
        d1.save()
        d2, _ = Domain.objects.get_or_create(name="private.corp.phx1.mozilla.com")
        d2.soa = soa
        d2.save()

        d, _ = Domain.objects.get_or_create(name="arpa")
        d, _ = Domain.objects.get_or_create(name="in-addr.arpa")
        d, _ = Domain.objects.get_or_create(name="15.in-addr.arpa")
        n = Network(network_str="15.0.0.0/8", ip_type="4")
        n.clean()
        n.site = s1
        n.vlan = v
        n.save()

        r = Range(start_str="15.0.0.0", end_str="15.0.0.10",
                network=n)
        r.clean()
        r.save()

    def test1_create_ipv4_interface_from_range(self):
        intr, errors = create_ipv4_intr_from_range("foo",
                "private.corp.phx1.mozilla.com", self.system,
                "11:22:33:44:55:66", "15.0.0.1", "15.0.0.3")
        intr.save()
        self.assertEqual(errors, None)
        self.assertTrue(isinstance(intr, StaticInterface))
        self.assertEqual(intr.ip_str, "15.0.0.1")

    def test2_create_ipv4_interface_from_range(self):
        # test soa inherit
        intr, errors = create_ipv4_intr_from_range("foo",
                "superprivate.corp.phx1.mozilla.com", self.system,
                "11:22:33:44:55:66", "15.0.0.20", "15.0.0.22")
        intr.save()
        self.assertEqual(errors, None)
        self.assertTrue(isinstance(intr, StaticInterface))
        self.assertEqual(intr.ip_str, "15.0.0.20")
        self.assertEqual(intr.domain.soa, self.s)
        self.assertEqual(intr.domain.name, "superprivate.corp.phx1.mozilla.com")

    def test3_create_ipv4_interface_from_range(self):
        # Test for an error when all the IP's are in use.
        intr, errors = create_ipv4_intr_from_range("foo",
                "private.corp.phx1.mozilla.com", self.system,
                "11:22:33:44:55:66", "15.0.0.2", "15.0.0.5")
        intr.save()
        self.assertEqual(errors, None)
        self.assertTrue(isinstance(intr, StaticInterface))
        self.assertEqual(intr.ip_str, "15.0.0.2")

        intr, errors = create_ipv4_intr_from_range("foo",
                "private.corp.phx1.mozilla.com", self.system,
                "11:22:33:44:55:66", "15.0.0.2", "15.0.0.5")
        intr.save()
        self.assertEqual(errors, None)
        self.assertTrue(isinstance(intr, StaticInterface))
        self.assertEqual(intr.ip_str, "15.0.0.3")

        intr, errors = create_ipv4_intr_from_range("foo",
                "private.corp.phx1.mozilla.com", self.system,
                "11:22:33:44:55:66", "15.0.0.2", "15.0.0.5")
        intr.save()
        self.assertEqual(errors, None)
        self.assertTrue(isinstance(intr, StaticInterface))
        self.assertEqual(intr.ip_str, "15.0.0.4")

        intr, errors = create_ipv4_intr_from_range("foo",
                "private.corp.phx1.mozilla.com", self.system,
                "11:22:33:44:55:66", "15.0.0.2", "15.0.0.5")
        intr.save()
        self.assertEqual(errors, None)
        self.assertTrue(isinstance(intr, StaticInterface))
        self.assertEqual(intr.ip_str, "15.0.0.5")

        intr, errors = create_ipv4_intr_from_range("foo",
                "private.corp.phx1.mozilla.com", self.system,
                "11:22:33:44:55:66", "15.0.0.2", "15.0.0.5")
        self.assertEqual(intr, None)
        self.assertTrue("ip" in errors)
