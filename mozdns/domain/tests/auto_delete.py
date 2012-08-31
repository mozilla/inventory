from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.test import TestCase

from systems.models import System
from mozdns.address_record.models import AddressRecord
from core.interface.static_intr.models import StaticInterface
from mozdns.cname.models import CNAME
from mozdns.ptr.models import PTR
from mozdns.txt.models import TXT
from mozdns.mx.models import MX
from mozdns.srv.models import SRV
from mozdns.domain.models import Domain
from mozdns.domain.models import ValidationError, _name_to_domain
from mozdns.ip.models import ipv6_to_longs, Ip
from mozdns.nameserver.models import Nameserver
from mozdns.domain.models import Domain
from mozdns.utils import ensure_label_domain, prune_tree
from mozdns.soa.models import SOA

from core.site.models import Site

import pdb

class AutoDeleteTests(TestCase):

    def setUp(self):
        s, _ = SOA.objects.get_or_create(primary="foo", contact="Foo",
                comment="foo")
        self.c = Domain(name = 'poo')
        self.c.save()
        self.assertFalse(self.c.purgeable)
        self.f_c = Domain(name = 'foo.poo')
        self.f_c.soa = s
        self.f_c.save()

    def test_cleanup_txt(self):
        self.assertFalse(Domain.objects.filter(name="x.y.z.foo.poo"))
        self.assertFalse(Domain.objects.filter(name="y.z.foo.poo"))
        self.assertFalse(Domain.objects.filter(name="z.foo.poo"))
        self.assertTrue(Domain.objects.filter(name="foo.poo"))

        self.assertFalse(self.f_c.purgeable)
        fqdn = "bar.x.y.z.foo.poo"
        label, the_domain = ensure_label_domain(fqdn)

        txt = TXT(label=label, domain=the_domain, txt_data="Nthing")
        txt.save()
        self.assertFalse(prune_tree(the_domain))
        txt.delete()

        self.assertFalse(Domain.objects.filter(name="x.y.z.foo.poo"))
        self.assertFalse(Domain.objects.filter(name="y.z.foo.poo"))
        self.assertFalse(Domain.objects.filter(name="z.foo.poo"))
        self.assertTrue(Domain.objects.filter(name="foo.poo"))

    def test_cleanup_address(self):
        self.assertFalse(Domain.objects.filter(name="x.y.z.foo.poo"))
        self.assertFalse(Domain.objects.filter(name="y.z.foo.poo"))
        self.assertFalse(Domain.objects.filter(name="z.foo.poo"))
        self.assertTrue(Domain.objects.filter(name="foo.poo"))

        fqdn = "bar.x.y.z.foo.poo"
        label, the_domain = ensure_label_domain(fqdn)
        addr = AddressRecord(label=label, domain=the_domain,
                ip_type='4', ip_str="10.2.3.4")
        addr.save()
        self.assertFalse(prune_tree(the_domain))
        addr.delete()

        self.assertFalse(Domain.objects.filter(name="x.y.z.foo.poo"))
        self.assertFalse(Domain.objects.filter(name="y.z.foo.poo"))
        self.assertFalse(Domain.objects.filter(name="z.foo.poo"))
        self.assertTrue(Domain.objects.filter(name="foo.poo"))

    def test_cleanup_mx(self):
        self.assertFalse(Domain.objects.filter(name="x.y.z.foo.poo"))
        self.assertFalse(Domain.objects.filter(name="y.z.foo.poo"))
        self.assertFalse(Domain.objects.filter(name="z.foo.poo"))
        self.assertTrue(Domain.objects.filter(name="foo.poo"))

        fqdn = "bar.x.y.z.foo.poo"
        label, the_domain = ensure_label_domain(fqdn)
        mx = MX(label=label, domain=the_domain, server="foo", priority=4)
        mx.save()
        self.assertFalse(prune_tree(the_domain))
        mx.delete()

        self.assertFalse(Domain.objects.filter(name="x.y.z.foo.poo"))
        self.assertFalse(Domain.objects.filter(name="y.z.foo.poo"))
        self.assertFalse(Domain.objects.filter(name="z.foo.poo"))
        self.assertTrue(Domain.objects.filter(name="foo.poo"))

    def test_ns_cleanup(self):
        self.assertFalse(Domain.objects.filter(name="x.y.z.foo.poo"))
        self.assertFalse(Domain.objects.filter(name="y.z.foo.poo"))
        self.assertFalse(Domain.objects.filter(name="z.foo.poo"))
        self.assertTrue(Domain.objects.filter(name="foo.poo"))

        fqdn = "bar.x.y.z.foo.poo"
        label, the_domain = ensure_label_domain(fqdn)
        ns = Nameserver(domain=the_domain, server="asdfasffoo")
        ns.save()
        self.assertFalse(prune_tree(the_domain))
        ns.delete()

        self.assertFalse(Domain.objects.filter(name="x.y.z.foo.poo"))
        self.assertFalse(Domain.objects.filter(name="y.z.foo.poo"))
        self.assertFalse(Domain.objects.filter(name="z.foo.poo"))
        self.assertTrue(Domain.objects.filter(name="foo.poo"))

    def test_srv_cleanup(self):
        self.assertFalse(Domain.objects.filter(name="x.y.z.foo.poo"))
        self.assertFalse(Domain.objects.filter(name="y.z.foo.poo"))
        self.assertFalse(Domain.objects.filter(name="z.foo.poo"))
        self.assertTrue(Domain.objects.filter(name="foo.poo"))

        fqdn = "bar.x.y.z.foo.poo"
        label, the_domain = ensure_label_domain(fqdn)
        srv = SRV(label='_'+label, domain=the_domain, target="foo", priority=4,
                weight=4, port=34)
        srv.save()
        self.assertFalse(prune_tree(the_domain))
        srv.delete()

        self.assertFalse(Domain.objects.filter(name="x.y.z.foo.poo"))
        self.assertFalse(Domain.objects.filter(name="y.z.foo.poo"))
        self.assertFalse(Domain.objects.filter(name="z.foo.poo"))
        self.assertTrue(Domain.objects.filter(name="foo.poo"))

    def test_cleanup_cname(self):
        # Make sure CNAME record block
        c = Domain(name = 'foo1')
        c.save()
        self.assertFalse(c.purgeable)
        s, _ = SOA.objects.get_or_create(primary="foo", contact="Foo",
                comment="dddfoo")
        f_c = Domain(name = 'foo.foo1')
        f_c.soa = s
        f_c.save()

        self.assertFalse(Domain.objects.filter(name="x.y.z.foo.foo1"))
        self.assertFalse(Domain.objects.filter(name="y.z.foo.foo1"))
        self.assertFalse(Domain.objects.filter(name="z.foo.foo1"))
        self.assertTrue(Domain.objects.filter(name="foo.foo1"))

        self.assertFalse(f_c.purgeable)
        fqdn = "cname.x.y.z.foo.foo1"
        label, the_domain = ensure_label_domain(fqdn)

        cname = CNAME(label=label, domain=the_domain, target="foo")
        cname.save()
        self.assertFalse(prune_tree(the_domain))
        cname.delete()

        self.assertFalse(Domain.objects.filter(name="x.y.z.foo.foo1"))
        self.assertFalse(Domain.objects.filter(name="y.z.foo.foo1"))
        self.assertFalse(Domain.objects.filter(name="z.foo.foo1"))
        fqdn = "bar.x.y.z.foo.poo"
        self.assertTrue(Domain.objects.filter(name="foo.foo1"))

    def test_cleanup_intr(self):
        self.assertFalse(Domain.objects.filter(name="x.y.z.foo.poo"))
        self.assertFalse(Domain.objects.filter(name="y.z.foo.poo"))
        self.assertFalse(Domain.objects.filter(name="z.foo.poo"))
        self.assertTrue(Domain.objects.filter(name="foo.poo"))

        Domain.objects.get_or_create(name="arpa")
        Domain.objects.get_or_create(name="in-addr.arpa")
        Domain.objects.get_or_create(name="10.in-addr.arpa")

        fqdn = "bar.x.y.z.foo.poo"
        label, the_domain = ensure_label_domain(fqdn)
        system = System()
        addr = StaticInterface(label=label, domain=the_domain,
                ip_type='4', ip_str="10.2.3.4", mac="00:11:22:33:44:55",
                system=system)
        addr.save()
        self.assertFalse(prune_tree(the_domain))
        addr.delete()

        self.assertFalse(Domain.objects.filter(name="x.y.z.foo.poo"))
        self.assertFalse(Domain.objects.filter(name="y.z.foo.poo"))
        self.assertFalse(Domain.objects.filter(name="z.foo.poo"))
        self.assertTrue(Domain.objects.filter(name="foo.poo"))
