from django.test import TestCase
from django.core.exceptions import ValidationError

from core.registration.static.models import StaticReg
from systems.tests.utils import create_fake_host
from mozdns.domain.models import Domain
from mozdns.address_record.models import AddressRecord
from mozdns.ptr.models import PTR

from mozdns.ip.utils import ip_to_domain_name


class V6StaticStaticRegTests(TestCase):
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
        self.arpa = self.create_domain(name='arpa')
        self.arpa.save()
        self.i_arpa = self.create_domain(name='ip6.arpa', ip_type='6')
        self.i_arpa.save()

        self.c = Domain(name="ccc")
        self.c.save()
        self.f_c = Domain(name="foo.ccc")
        self.f_c.save()
        self.r1 = self.create_domain(name="0", ip_type='6')
        self.r1.save()
        self.r2 = self.create_domain(name="1", ip_type='6')
        self.r2.save()
        self.n = create_fake_host(hostname="foo.mozilla.com")
        self.n.clean()
        self.n.save()

    def do_add(self, label, domain, ip_str, ip_type='6'):
        r = StaticReg(
            label=label, domain=domain, ip_str=ip_str,
            ip_type=ip_type, system=self.n
        )
        r.clean()
        r.save()
        repr(r)
        return r

    def do_delete(self, r):
        ip_str = r.ip_str
        fqdn = r.fqdn
        r.delete()
        self.assertFalse(
            AddressRecord.objects.filter(ip_str=ip_str, fqdn=fqdn))

    def test1_create_basic(self):
        label = "foo"
        domain = self.f_c
        ip_str = "12::11:22:33:44:55:66"
        kwargs = {'label': label, 'domain': domain,
                  'ip_str': ip_str}
        self.do_add(**kwargs)

    def test2_create_basic(self):
        label = "foo1"
        domain = self.f_c
        ip_str = "123::20:22:33:44:55:66"
        kwargs = {'label': label, 'domain': domain,
                  'ip_str': ip_str}
        self.do_add(**kwargs)

    def test3_create_basic(self):
        label = "foo1"
        domain = self.f_c
        ip_str = "1234::11:22:33:44:55:66"
        kwargs = {'label': label, 'domain': domain,
                  'ip_str': ip_str}
        self.do_add(**kwargs)

    def test4_create_basic(self):
        label = "foo1"
        domain = self.f_c
        ip_str = "11::12:22:33:44:55:66"
        kwargs = {'label': label, 'domain': domain,
                  'ip_str': ip_str}
        self.do_add(**kwargs)

    def test1_delete(self):
        label = "foo1"
        domain = self.f_c
        ip_str = "112::12:22:33:44:55:66"
        kwargs = {'label': label, 'domain': domain,
                  'ip_str': ip_str}
        r = self.do_add(**kwargs)
        self.do_delete(r)

    def test1_dup_create_basic(self):
        label = "foo3"
        domain = self.f_c
        ip_str = "1123::11:22:33:44:55:66"
        kwargs = {'label': label, 'domain': domain,
                  'ip_str': ip_str}
        self.do_add(**kwargs)
        self.assertRaises(ValidationError, self.do_add, **kwargs)

    def test1_bad_add_for_a_ptr(self):
        # StaticReg exists, then try ptr and A
        label = "9988fooddfdf"
        domain = self.c
        ip_str = "111::11:22:33:44:55:6e"
        kwargs = {'label': label, 'domain': domain,
                  'ip_str': ip_str}
        ip_type = '6'
        i = self.do_add(**kwargs)
        i.clean()
        i.save()
        a = AddressRecord(label=label, domain=domain, ip_str=ip_str,
                          ip_type=ip_type)
        self.assertRaises(ValidationError, a.clean)
        ptr = PTR(ip_str=ip_str, ip_type=ip_type, name=i.fqdn)
        self.assertRaises(ValidationError, ptr.clean)

    def test2_bad_add_for_a_ptr(self):
        # PTR and A exist, then try add sreg
        label = "9988fdfood"
        domain = self.c
        ip_str = "1112::11:22:33:44:55:66"
        kwargs = {'label': label, 'domain': domain,
                  'ip_str': ip_str}
        ip_type = '6'
        a = AddressRecord(label=label, domain=domain, ip_str=ip_str,
                          ip_type=ip_type)
        a.clean()
        a.save()
        ptr = PTR(ip_str=ip_str, ip_type=ip_type, name=a.fqdn)
        ptr.clean()
        ptr.save()
        self.assertRaises(ValidationError, self.do_add, **kwargs)

    def test1_bad_reverse_domain(self):
        label = "8888foo"
        domain = self.f_c
        ip_str = "115::11:22:33:44:55:66"
        kwargs = {'label': label, 'domain': domain,
                  'ip_str': ip_str}
        i = self.do_add(**kwargs)
        i.ip_str = "9111::"
        self.assertRaises(ValidationError, i.save)

    def test1_no_system(self):
        label = "8888foo"
        domain = self.f_c
        ip_str = "188::15:22:33:44:55:66"
        ip_type = '6'
        r = StaticReg(
            label=label, domain=domain, ip_str=ip_str, ip_type=ip_type,
            system=None)
        self.assertRaises(ValidationError, r.clean)
