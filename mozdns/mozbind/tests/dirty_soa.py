from django.test import TestCase

from mozdns.soa.models import SOA
from mozdns.srv.models import SRV
from mozdns.txt.models import TXT
from mozdns.ptr.models import PTR
from mozdns.mx.models import MX
from mozdns.cname.models import CNAME
from mozdns.address_record.models import AddressRecord
from mozdns.nameserver.models import Nameserver
from mozdns.tests.utils import create_fake_zone

from core.interface.static_intr.models import StaticInterface

from systems.models import System
from core.task.models import Task


class DirtySOATests(TestCase):
    def setUp(self):
        self.r1 = create_fake_zone("10.in-addr.arpa", suffix="")
        self.sr = self.r1.soa
        self.sr.dirty = False
        self.sr.save()

        self.dom = create_fake_zone("bgaz", suffix="")
        self.soa = self.dom.soa
        self.soa.dirty = False
        self.soa.save()

        self.rdom = create_fake_zone("123.in-addr.arpa", suffix="")
        self.rsoa = self.r1.soa
        self.rsoa.dirty = False
        self.rsoa.save()

        self.s = System()
        self.s.save()

    def test_print_soa(self):
        self.assertTrue(self.soa.bind_render_record() not in ('', None))
        self.assertTrue(self.rsoa.bind_render_record() not in ('', None))

    def generic_dirty(self, Klass, create_data, update_data, local_soa):
        Task.dns.all().delete()  # Delete all tasks
        local_soa.dirty = False
        local_soa.save()
        rec = Klass(**create_data)
        rec.full_clean()
        rec.save()
        self.assertTrue(rec.bind_render_record() not in ('', None))
        local_soa = SOA.objects.get(pk=local_soa.pk)
        self.assertTrue(local_soa.dirty)

        self.assertEqual(1, Task.dns.all().count())

        # Now try updating
        Task.dns.all().delete()  # Delete all tasks
        local_soa.dirty = False
        local_soa.save()
        local_soa = SOA.objects.get(pk=local_soa.pk)
        self.assertFalse(local_soa.dirty)
        for k, v in update_data.iteritems():
            setattr(rec, k, v)
        rec.save()
        local_soa = SOA.objects.get(pk=local_soa.pk)
        self.assertTrue(local_soa.dirty)

        self.assertEqual(1, Task.dns.all().count())

        # Now delete
        Task.dns.all().delete()  # Delete all tasks
        local_soa.dirty = False
        local_soa.save()
        local_soa = SOA.objects.get(pk=local_soa.pk)
        self.assertFalse(local_soa.dirty)
        rec.delete()
        local_soa = SOA.objects.get(pk=local_soa.pk)
        self.assertTrue(local_soa.dirty)

        self.assertEqual(1, Task.dns.all().count())

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
