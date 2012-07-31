"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.core.exceptions import ValidationError

from mozdns.soa.models import SOA
from mozdns.domain.models import Domain
from mozdns.mx.models import MX
from mozdns.srv.models import SRV
from mozdns.txt.models import TXT
from mozdns.cname.models import CNAME
from mozdns.address_record.models import AddressRecord

from core.interface.static_intr.models import StaticInterface
from mozdns.ip.utils import ip2dns_form

from systems.models import System

import pdb


class CNAMETests(TestCase):

    def create_domain(self, name, ip_type=None, delegated=False):
        if ip_type is None:
            ip_type = '4'
        if name in ('arpa', 'in-addr.arpa', 'ipv6.arpa'):
            pass
        else:
            name = ip2dns_form(name, ip_type=ip_type)
        d = Domain(name = name, delegated=delegated)
        d.clean()
        self.assertTrue(d.is_reverse)
        return d


    def setUp(self):
        primary = "ns5.oregonstate.edu"
        contact = "admin.oregonstate.edu"
        retry = 1234
        refresh = 1234123
        self.soa = SOA(primary = primary, contact = contact, retry = retry, refresh = refresh)
        self.soa.save()

        self.g = Domain(name = "gz")
        self.g.save()
        self.c_g = Domain(name = "coo.gz")
        self.c_g.soa = self.soa
        self.c_g.save()
        self.d = Domain(name = "dz")
        self.d.save()

        self.arpa = self.create_domain( name = 'arpa')
        self.arpa.save()
        self.i_arpa = self.create_domain( name = 'in-addr.arpa')
        self.i_arpa.save()
        self.r1 = self.create_domain(name="10")
        self.r1.save()

        self.s = System()
        self.s.save()


    def do_add(self, label, domain, data):
        cn = CNAME(label = label, domain = domain, data = data)
        cn.full_clean()
        cn.save()
        cn.save()
        self.assertTrue(cn.get_absolute_url())
        self.assertTrue(cn.get_edit_url())
        self.assertTrue(cn.get_delete_url())
        self.assertTrue(cn.details())

        cs = CNAME.objects.filter(label = label, domain = domain, data = data)
        self.assertEqual(len(cs), 1)
        return cn

    def test_add(self):
        label = "foo"
        domain = self.g
        data = "foo.com"
        x = self.do_add(label, domain, data)

        label = "boo"
        domain = self.c_g
        data = "foo.foo.com"
        self.do_add(label, domain, data)

        label = "fo1"
        domain = self.g
        data = "foo.com"
        self.do_add(label, domain, data)
        self.assertRaises(ValidationError, self.do_add, *(label, domain, data))

        label = ""
        domain = self.g
        data = "foo.com"
        self.do_add(label, domain, data)

    def test1_add_glob(self):
        label = "*foo"
        domain = self.g
        data = "foo.com"
        x = self.do_add(label, domain, data)

        label = "*"
        domain = self.c_g
        data = "foo.foo.com"
        self.do_add(label, domain, data)

        label = "*.fo1"
        domain = self.g
        data = "foo.com"
        self.assertRaises(ValidationError, self.do_add, *(label, domain, data))

        label = "*sadfasfd-asdf"
        domain = self.g
        data = "foo.com"
        self.do_add(label, domain, data)

    def test2_add_glob(self):
        label = "*coo"
        domain = self.g
        data = "foo.com"
        x = self.do_add(label, domain, data)

        label = "*"
        domain = self.c_g
        data = "foo.com"
        x = self.do_add(label, domain, data)

    def test_soa_condition(self):
        label = ""
        domain = self.c_g
        data = "foo.com"
        self.assertRaises(ValidationError, self.do_add, *(label, domain, data))

    def test_data_domain(self):
        label = "fo1"
        domain = self.g
        data = "foo.dz"
        cn = self.do_add(label, domain, data)

        self.assertTrue(self.d == cn.data_domain)

    def test_add_bad(self):
        label = ""
        domain = self.g
        data = "..foo.com"
        self.assertRaises(ValidationError, self.do_add, *(label, domain, data))

    def test_add_mx_with_cname(self):
        label = "cnamederp1"
        domain = self.c_g
        data = "foo.com"

        fqdn = label+'.'+domain.name
        data = { 'label':'' ,'domain':self.c_g ,'server':fqdn ,'priority':2 ,'ttl':2222 }
        mx = MX(**data)
        mx.save()

        cn = CNAME(label = label, domain = domain, data = data)

        self.assertRaises(ValidationError, cn.full_clean)

    def test_address_record_exists(self):
        label = "testyfoo"
        data = "wat"
        dom,_ = Domain.objects.get_or_create(name="cd")
        dom,_ = Domain.objects.get_or_create(name="what.cd")

        rec, _ = AddressRecord.objects.get_or_create(label=label, domain=dom, ip_type='4', ip_str="128.193.1.1")

        cn = CNAME(label = label, domain = dom, data = data)
        self.assertRaises(ValidationError, cn.full_clean)

    def test_address_record_cname_exists(self):
        label = "testyfoo"
        data = "wat"
        dom,_ = Domain.objects.get_or_create(name="cd")
        dom,_ = Domain.objects.get_or_create(name="what.cd")

        cn = CNAME.objects.get_or_create(label = label, domain = dom, data = data)
        rec = AddressRecord(label=label, domain=dom, ip_str="128.193.1.1")

        self.assertRaises(ValidationError, rec.save)

    def test_srv_exists(self):
        label = "_testyfoo"
        data = "wat"
        dom,_ = Domain.objects.get_or_create(name="cd")
        dom,_ = Domain.objects.get_or_create(name="what.cd")

        rec, _ = SRV.objects.get_or_create(label=label, domain=dom, target="asdf", \
                                            port=2, priority=2, weight=4)

        cn = CNAME(label = label, domain = dom, data = data)
        self.assertRaises(ValidationError, cn.full_clean)

    def test_srv_cname_exists(self):
        label = "testyfoo"
        data = "wat"
        dom,_ = Domain.objects.get_or_create(name="cd")
        dom,_ = Domain.objects.get_or_create(name="what.cd")

        cn = CNAME.objects.get_or_create(label = label, domain = dom, data = data)

        rec = SRV(label=label, domain=dom, target="asdf", \
                                            port=2, priority=2, weight=4)

        self.assertRaises(ValidationError, rec.save)

    def test_txt_exists(self):
        label = "testyfoo"
        data = "wat"
        dom,_ = Domain.objects.get_or_create(name="cd")
        dom,_ = Domain.objects.get_or_create(name="what.cd")

        rec, _ = TXT.objects.get_or_create(label=label, domain=dom, txt_data="asdf")

        cn = CNAME(label = label, domain = dom, data = data)
        self.assertRaises(ValidationError, cn.full_clean)

    def test_txt_cname_exists(self):
        label = "testyfoo"
        data = "wat"
        dom,_ = Domain.objects.get_or_create(name="cd")
        dom,_ = Domain.objects.get_or_create(name="what.cd")

        cn,_ = CNAME.objects.get_or_create(label = label, domain = dom, data = data)
        cn.full_clean()
        cn.save()

        rec = TXT(label=label, domain=dom, txt_data="asdf1")

        self.assertRaises(ValidationError, rec.save)

    def test_mx_exists(self):
        label = "testyfoo"
        data = "wat"
        dom,_ = Domain.objects.get_or_create(name="cd")
        dom,_ = Domain.objects.get_or_create(name="what.cd")

        rec, _ = MX.objects.get_or_create(label=label, domain=dom, server="asdf",\
                                            priority=123, ttl=123)

        cn = CNAME(label = label, domain = dom, data = data)
        self.assertRaises(ValidationError, cn.full_clean)

    def test_mx_cname_exists(self):
        # Duplicate test?
        label = "testyfoo"
        data = "wat"
        dom,_ = Domain.objects.get_or_create(name="cd")
        dom,_ = Domain.objects.get_or_create(name="what.cd")

        cn,_ = CNAME.objects.get_or_create(label = label, domain = dom, data = data)
        cn.full_clean()
        cn.save()

        rec = MX(label=label, domain=dom, server="asdf1",\
                                            priority=123, ttl=123)

        self.assertRaises(ValidationError, rec.save)

    def test_intr_exists(self):
        label = "tdfestyfoo"
        data = "waasdft"
        dom,_ = Domain.objects.get_or_create(name="cd")
        dom,_ = Domain.objects.get_or_create(name="what.cd")

        intr = StaticInterface(label=label, domain=dom, ip_str = "10.0.0.1",
                ip_type='4', system=self.s, mac="11:22:33:44:55:66")
        intr.clean()
        intr.save()

        cn = CNAME(label = label, domain = dom, data = data)
        self.assertRaises(ValidationError, cn.full_clean)

    def test_intr_cname_exists(self):
        # Duplicate test?
        label = "tesafstyfoo"
        data = "wadfakt"
        dom,_ = Domain.objects.get_or_create(name="cd")
        dom,_ = Domain.objects.get_or_create(name="what.cd")

        cn,_ = CNAME.objects.get_or_create(label = label, domain = dom, data = data)
        cn.full_clean()
        cn.save()

        intr = StaticInterface(label=label, domain=dom, ip_str = "10.0.0.2",
                ip_type='4')

        self.assertRaises(ValidationError, intr.clean)
