from django.test import TestCase
from django.core.exceptions import ValidationError

from mozdns.domain.models import Domain
from mozdns.nameserver.models import Nameserver
from mozdns.mx.models import MX
from mozdns.srv.models import SRV
from mozdns.txt.models import TXT
from mozdns.ptr.models import PTR
from mozdns.cname.models import CNAME
from mozdns.address_record.models import AddressRecord

from core.interface.static_intr.models import StaticInterface
from mozdns.ip.utils import ip_to_domain_name

from systems.models import System
from mozdns.tests.utils import create_fake_zone


class CNAMETests(TestCase):

    def create_domain(self, name, ip_type=None, delegated=False):
        if ip_type is None:
            ip_type = '4'
        if name in ('arpa', 'in-addr.arpa', 'ip6.arpa'):
            pass
        else:
            name = ip_to_domain_name(name, ip_type=ip_type)
        d = Domain(name=name, delegated=delegated)
        d.clean()
        self.assertTrue(d.is_reverse)
        return d

    def setUp(self):
        self.g = create_fake_zone("gz", suffix="")
        self.c_g = create_fake_zone("coo.gz", suffix="")
        self.d = create_fake_zone("dz", suffix="")

        self.r1 = create_fake_zone("10.in-addr.arpa", suffix="")
        self.r1.save()

        self.s = System()
        self.s.save()

    def do_add(self, label, domain, data):
        cn = CNAME(label=label, domain=domain, target=data)
        cn.full_clean()
        cn.save()
        cn.save()
        self.assertTrue(cn.get_absolute_url())
        self.assertTrue(cn.get_edit_url())
        self.assertTrue(cn.get_delete_url())
        self.assertTrue(cn.details())

        cs = CNAME.objects.filter(
            label=label, domain=domain, target=data)
        self.assertEqual(len(cs), 1)
        return cn

    def test_add(self):
        label = "foo"
        domain = self.g
        data = "foo.com"
        self.do_add(label, domain, data)

        label = "boo"
        domain = self.c_g
        data = "foo.foo.com"
        self.do_add(label, domain, data)

        label = "fo1"
        domain = self.g
        data = "foo.com"
        self.do_add(label, domain, data)
        self.assertRaises(ValidationError, self.do_add, *(label, domain, data))

        label = "adsf"
        domain = self.c_g
        data = "foo.com"
        self.do_add(label, domain, data)

    def test1_add_glob(self):
        label = "*foo"
        domain = self.g
        data = "foo.com"
        self.do_add(label, domain, data)

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
        self.do_add(label, domain, data)

        label = "*"
        domain = self.c_g
        data = "foo.com"
        self.do_add(label, domain, data)

    def test_soa_condition(self):
        label = ""
        domain = self.c_g
        data = "foo.com"
        self.assertRaises(ValidationError, self.do_add, *(label, domain, data))

    def test_add_bad(self):
        label = ""
        domain = self.g
        data = "..foo.com"
        self.assertRaises(ValidationError, self.do_add, *(label, domain, data))

    def test_add_mx_with_cname(self):
        label = "cnamederp1"
        domain = self.c_g
        data = "foo.com"

        fqdn = label + '.' + domain.name
        mx_data = {'label': '', 'domain': self.c_g, 'server':
                   fqdn, 'priority': 2, 'ttl': 2222}
        mx = MX(**mx_data)
        mx.save()

        cn = CNAME(label=label, domain=domain, target=data)

        self.assertRaises(ValidationError, cn.full_clean)

    def test_address_record_exists(self):
        label = "testyfoo"
        data = "wat"
        dom, _ = Domain.objects.get_or_create(name="cd")
        dom, _ = Domain.objects.get_or_create(name="what.cd")

        rec, _ = AddressRecord.objects.get_or_create(
            label=label, domain=dom, ip_type='4', ip_str="128.193.1.1")

        cn = CNAME(label=label, domain=dom, target=data)
        self.assertRaises(ValidationError, cn.full_clean)

    def test_address_record_exists_upper_case(self):
        label = "testyfoo"
        data = "wat"
        dom, _ = Domain.objects.get_or_create(name="cd")
        dom, _ = Domain.objects.get_or_create(name="what.cd")

        rec, _ = AddressRecord.objects.get_or_create(
            label=label, domain=dom, ip_type='4', ip_str="128.193.1.1")

        cn = CNAME(label=label.title(), domain=dom, target=data)
        self.assertRaises(ValidationError, cn.full_clean)

    def test_address_record_cname_exists(self):
        label = "testyfoo"
        data = "wat"
        dom, _ = Domain.objects.get_or_create(name="cd")
        dom, _ = Domain.objects.get_or_create(name="what.cd")

        CNAME.objects.get_or_create(label=label, domain=dom, target=data)
        rec = AddressRecord(label=label, domain=dom, ip_str="128.193.1.1")

        self.assertRaises(ValidationError, rec.save)

    def test_address_record_cname_exists_upper(self):
        label = "testyfoo"
        data = "wat"
        dom, _ = Domain.objects.get_or_create(name="cd")
        dom, _ = Domain.objects.get_or_create(name="what.cd")

        CNAME.objects.get_or_create(label=label, domain=dom, target=data)
        rec = AddressRecord(
            label=label.title(), domain=dom, ip_str="128.193.1.1")

        self.assertRaises(ValidationError, rec.save)

    def test_srv_exists(self):
        label = "_testyfoo"
        data = "wat"
        dom, _ = Domain.objects.get_or_create(name="cd")
        dom, _ = Domain.objects.get_or_create(name="what.cd")

        rec, _ = SRV.objects.get_or_create(
            label=label, domain=dom, target="asdf",
                                            port=2, priority=2, weight=4)

        cn = CNAME(label=label, domain=dom, target=data)
        self.assertRaises(ValidationError, cn.full_clean)

    def test_srv_cname_exists(self):
        label = "testyfoo"
        data = "wat"
        dom, _ = Domain.objects.get_or_create(name="cd")
        dom, _ = Domain.objects.get_or_create(name="what.cd")

        CNAME.objects.get_or_create(
            label=label, domain=dom, target=data)

        rec = SRV(label=label, domain=dom, target="asdf",
                  port=2, priority=2, weight=4)

        self.assertRaises(ValidationError, rec.save)

    def test_txt_exists(self):
        label = "testyfoo"
        data = "wat"
        dom, _ = Domain.objects.get_or_create(name="cd")
        dom, _ = Domain.objects.get_or_create(name="what.cd")

        rec, _ = TXT.objects.get_or_create(
            label=label, domain=dom, txt_data="asdf")

        cn = CNAME(label=label, domain=dom, target=data)
        self.assertRaises(ValidationError, cn.full_clean)

    def test_txt_cname_exists(self):
        label = "testyfoo"
        data = "wat"
        dom, _ = Domain.objects.get_or_create(name="cd")
        dom, _ = Domain.objects.get_or_create(name="what.cd")

        cn, _ = CNAME.objects.get_or_create(
            label=label, domain=dom, target=data)
        cn.full_clean()
        cn.save()

        rec = TXT(label=label, domain=dom, txt_data="asdf1")

        self.assertRaises(ValidationError, rec.save)

    def test_mx_exists(self):
        label = "testyfoo"
        data = "wat"
        dom, _ = Domain.objects.get_or_create(name="cd")
        dom, _ = Domain.objects.get_or_create(name="what.cd")

        rec, _ = MX.objects.get_or_create(
            label=label, domain=dom, server="asdf",
                                            priority=123, ttl=123)

        cn = CNAME(label=label, domain=dom, target=data)
        self.assertRaises(ValidationError, cn.full_clean)

    def test_mx_cname_exists(self):
        # Duplicate test?
        label = "testyfoo"
        data = "wat"
        dom, _ = Domain.objects.get_or_create(name="cd")
        dom, _ = Domain.objects.get_or_create(name="what.cd")

        cn, _ = CNAME.objects.get_or_create(
            label=label, domain=dom, target=data)
        cn.full_clean()
        cn.save()

        rec = MX(label=label, domain=dom, server="asdf1",
                 priority=123, ttl=123)

        self.assertRaises(ValidationError, rec.save)

    def test_ns_exists(self):
        # Duplicate test?
        data = "wat"
        dom, _ = Domain.objects.get_or_create(name="cd")
        dom, _ = Domain.objects.get_or_create(name="what.cd")

        rec = Nameserver(domain=dom, server="asdf1")
        rec.save()
        cn = CNAME(label='', domain=dom, target=data)
        self.assertRaises(ValidationError, cn.clean)

    def test_ns_cname_exists(self):
        # Duplicate test?
        data = "wat"
        dom, _ = Domain.objects.get_or_create(name="cd")
        dom, _ = Domain.objects.get_or_create(name="what.cd")

        cn, _ = CNAME.objects.get_or_create(
            label='', domain=dom, target=data)
        cn.full_clean()
        cn.save()

        rec = Nameserver(domain=dom, server="asdf1")
        self.assertRaises(ValidationError, rec.save)

    def test_intr_exists(self):
        label = "tdfestyfoo"
        data = "waasdft"
        dom, _ = Domain.objects.get_or_create(name="cd")
        dom, _ = Domain.objects.get_or_create(name="what.cd")

        intr = StaticInterface(label=label, domain=dom, ip_str="10.0.0.1",
                               ip_type='4', system=self.s,
                               mac="11:22:33:44:55:66")
        intr.clean()
        intr.save()

        cn = CNAME(label=label, domain=dom, target=data)
        self.assertRaises(ValidationError, cn.full_clean)

    def test_intr_cname_exists(self):
        # Duplicate test?
        label = "tesafstyfoo"
        data = "wadfakt"
        dom, _ = Domain.objects.get_or_create(name="cd")
        dom, _ = Domain.objects.get_or_create(name="what.cd")

        cn, _ = CNAME.objects.get_or_create(
            label=label, domain=dom, target=data)
        cn.full_clean()
        cn.save()

        intr = StaticInterface(label=label, domain=dom, ip_str="10.0.0.2",
                               ip_type='4', system=self.s,
                               mac="00:11:22:33:44:55")

        self.assertRaises(ValidationError, intr.clean)
        cn.label = "differentlabel"
        cn.save()
        intr.clean()
        intr.save()

    def test_ptr_exists(self):
        """
        Failing:
        see BUG https://bugzilla.mozilla.org/show_bug.cgi?id=810106
        """
        label = "testyfoo"
        data = "wat"
        dom, _ = Domain.objects.get_or_create(name="cd")
        dom, _ = Domain.objects.get_or_create(name="what.cd")

        rec = PTR(ip_str="10.193.1.1", ip_type='4', name='testyfoo.what.cd')
        rec.full_clean()
        rec.save()

        cn = CNAME(label=label, domain=dom, target=data)
        self.assertRaises(ValidationError, cn.full_clean)

    def test_ptr_cname_exists(self):
        """
        Failing:
        see BUG https://bugzilla.mozilla.org/show_bug.cgi?id=810106
        """
        label = "testyfoo"
        data = "wat"
        dom, _ = Domain.objects.get_or_create(name="cd")
        dom, _ = Domain.objects.get_or_create(name="what.cd")

        CNAME.objects.get_or_create(label=label, domain=dom, target=data)
        rec = PTR(ip_str="10.193.1.1", ip_type='4', name='testyfoo.what.cd')

        self.assertRaises(ValidationError, rec.clean)

    def test_cname_point_to_itself(self):
        label = "foopy"
        data = "foopy.what.cd"
        dom, _ = Domain.objects.get_or_create(name="cd")
        dom, _ = Domain.objects.get_or_create(name="what.cd")

        cn = CNAME(label=label, domain=dom, target=data)
        self.assertRaises(ValidationError, cn.clean)
