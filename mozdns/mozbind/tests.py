import sys
import os
import pdb

from django.test import TestCase

from mozdns.domain.models import Domain
from mozdns.soa.models import SOA
from mozdns.srv.models import SRV
from mozdns.txt.models import TXT
from mozdns.ptr.models import PTR
from mozdns.mx.models import MX
from mozdns.cname.models import CNAME
from mozdns.address_record.models import AddressRecord
from mozdns.nameserver.models import Nameserver
from core.interface.static_intr.models import StaticInterface
from mozdns.mozbind.build import *

from systems.models import System
import pdb

class DirtySOATests(TestCase):
    def setUp(self):
        Domain.objects.get_or_create(name="arpa")
        Domain.objects.get_or_create(name="in-addr.arpa")
        self.r1, _ = Domain.objects.get_or_create(name="10.in-addr.arpa")
        self.sr, sr_c = SOA.objects.get_or_create(primary = "ns1.foo.gaz", contact =
                "hostmaster.foo", comment="123foo.gazsdi2")
        self.r1.soa = self.sr
        self.r1.save()

        s1, s1_c = SOA.objects.get_or_create(primary = "ns1.foo.gaz", contact =
                "hostmaster.dfdfoo", comment="123fooasdfsdfasdfsa.gaz2")
        self.soa = s1
        d, _ = Domain.objects.get_or_create(name="bgaz")
        d.soa = s1
        d.save()
        self.dom = d
        self.soa.dirty = False
        self.dom.dirty = False

        s2, s1_c = SOA.objects.get_or_create(primary = "ns1.foo.gaz", contact =
                "hostmaster.foo", comment="123fooasdfsdf.gaz2")
        self.rsoa = s2
        rd, _ = Domain.objects.get_or_create(name="123.in-addr.arpa")
        rd.soa = s2
        rd.save()
        self.rdom = rd
        self.rsoa.dirty = False
        self.rdom.dirty = False

        self.s = System()
        self.s.save()

    def generic_dirty(self, Klass, create_data, update_data, local_soa):
        local_soa.dirty = False
        local_soa.save()
        rec = Klass(**create_data)
        rec.full_clean()
        rec.save()
        local_soa = SOA.objects.get(pk=local_soa.pk)
        self.assertTrue(local_soa.dirty)

        # Now try updating
        local_soa.dirty = False
        local_soa.save()
        local_soa = SOA.objects.get(pk=local_soa.pk)
        self.assertFalse(local_soa.dirty)
        for k, v in update_data.iteritems():
            setattr(rec, k, v)
        rec.save()
        local_soa = SOA.objects.get(pk=local_soa.pk)
        self.assertTrue(local_soa.dirty)



    def test_dirty_a(self):
        create_data = {
                        'label': 'asdf',
                        'domain': self.dom,
                        'ip_str': '10.2.3.1',
                        'ip_type': '4'
                    }
        update_data = {
                        'label': 'asdfx',
                    }
        self.generic_dirty(AddressRecord, create_data, update_data, self.soa)

    def test_dirty_intr(self):
        create_data = {
                        'label': 'asdf1',
                        'domain': self.dom,
                        'ip_str': '10.2.3.1',
                        'ip_type': '4',
                        'system': self.s,
                        'mac': '11:22:33:44:55:66'
                    }
        update_data = {
                        'label': 'asdfx1',
                    }
        self.generic_dirty(StaticInterface, create_data, update_data, self.soa)

    def test_dirty_cname(self):
        create_data = {
                        'label': 'asdf2',
                        'domain': self.dom,
                        'target': 'foo.bar.com',
                    }
        update_data = {
                        'label': 'asdfx2',
                    }
        self.generic_dirty(CNAME, create_data, update_data, self.soa)

    def test_dirty_ptr(self):
        create_data = {
                        'ip_str': '10.2.3.4',
                        'ip_type': '4',
                        'name': 'foo.bar.com',
                    }
        update_data = {
                        'label': 'asdfx2',
                    }
        self.generic_dirty(PTR, create_data, update_data, local_soa=self.sr)

    def test_dirty_mx(self):
        create_data = {
                        'label': '',
                        'domain': self.dom,
                        'priority': 10,
                        'server': 'foo.bar.com',
                    }
        update_data = {
                        'label': 'asdfx3',
                    }
        self.generic_dirty(MX, create_data, update_data, self.soa)

    def test_dirty_ns(self):
        create_data = {
                        'domain': self.dom,
                        'server': 'foo.bar.com',
                    }
        update_data = {
                        'label': 'asdfx4',
                    }
        self.generic_dirty(Nameserver, create_data, update_data, self.soa)

    def test_dirty_soa(self):
        self.soa.dirty = False
        self.soa.refresh = 123
        self.soa.save()
        self.assertTrue(self.soa.dirty)

    def test_dirty_srv(self):
        create_data = {
                        'label': '_asdf7',
                        'domain': self.dom,
                        'priority': 10,
                        'port': 10,
                        'weight': 10,
                        'target': 'foo.bar.com',
                    }
        update_data = {
                        'label': '_asdfx4',
                    }
        self.generic_dirty(SRV, create_data, update_data, self.soa)

    def test_dirty_txt(self):
        create_data = {
                        'label': 'asdf8',
                        'domain': self.dom,
                        'txt_data': 'some shit',
                    }
        update_data = {
                        'label': 'asdfx5',
                    }
        self.generic_dirty(TXT, create_data, update_data, self.soa)
