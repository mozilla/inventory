from django.test import TestCase
from django.core.exceptions import ValidationError

from core.interface.static_intr.models import StaticInterface
from systems.models import System
from mozdns.domain.models import Domain
from mozdns.address_record.models import AddressRecord
from mozdns.ptr.models import PTR

from mozdns.ip.utils import ip_to_domain_name


class V6StaticInterTests(TestCase):
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
        self.n = System()
        self.n.clean()
        self.n.save()

    def do_add(self, mac, label, domain, ip_str, ip_type='6'):
        r = StaticInterface(mac=mac, label=label, domain=domain, ip_str=ip_str,
                            ip_type=ip_type, system=self.n)
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
        mac = "11:22:33:44:55:66"
        label = "foo"
        domain = self.f_c
        ip_str = "12::" + mac
        kwargs = {'mac': mac, 'label': label, 'domain': domain,
                  'ip_str': ip_str}
        self.do_add(**kwargs)

    def test2_create_basic(self):
        mac = "20:22:33:44:55:66"
        label = "foo1"
        domain = self.f_c
        ip_str = "123::" + mac
        kwargs = {'mac': mac, 'label': label, 'domain': domain,
                  'ip_str': ip_str}
        self.do_add(**kwargs)

    def test3_create_basic(self):
        mac = "11:22:33:44:55:66"
        label = "foo1"
        domain = self.f_c
        ip_str = "1234::" + mac
        kwargs = {'mac': mac, 'label': label, 'domain': domain,
                  'ip_str': ip_str}
        self.do_add(**kwargs)

    def test4_create_basic(self):
        mac = "12:22:33:44:55:66"
        label = "foo1"
        domain = self.f_c
        ip_str = "11::" + mac
        kwargs = {'mac': mac, 'label': label, 'domain': domain,
                  'ip_str': ip_str}
        self.do_add(**kwargs)

    def test1_delete(self):
        mac = "12:22:33:44:55:66"
        label = "foo1"
        domain = self.f_c
        ip_str = "112::" + mac
        kwargs = {'mac': mac, 'label': label, 'domain': domain,
                  'ip_str': ip_str}
        r = self.do_add(**kwargs)
        self.do_delete(r)

    def test1_dup_create_basic(self):
        mac = "11:22:33:44:55:66"
        label = "foo3"
        domain = self.f_c
        ip_str = "1123::" + mac
        kwargs = {'mac': mac, 'label': label, 'domain': domain,
                  'ip_str': ip_str}
        self.do_add(**kwargs)
        self.assertRaises(ValidationError, self.do_add, **kwargs)

    def test1_bad_add_for_a_ptr(self):
        # Intr exists, then try ptr and A
        mac = "11:22:33:44:55:6e"
        label = "9988fooddfdf"
        domain = self.c
        ip_str = "111::" + mac
        kwargs = {'mac': mac, 'label': label, 'domain': domain,
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
        # PTR and A exist, then try add intr
        mac = "11:22:33:44:55:66"
        label = "9988fdfood"
        domain = self.c
        ip_str = "1112::" + mac
        kwargs = {'mac': mac, 'label': label, 'domain': domain,
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
        mac = "11:22:33:44:55:66"
        label = "8888foo"
        domain = self.f_c
        ip_str = "115::" + mac
        kwargs = {'mac': mac, 'label': label, 'domain': domain,
                  'ip_str': ip_str}
        i = self.do_add(**kwargs)
        i.ip_str = "9111::"
        self.assertRaises(ValidationError, i.clean)

    def test1_no_system(self):
        mac = "15:22:33:44:55:66"
        label = "8888foo"
        domain = self.f_c
        ip_str = "188::" + mac
        ip_type = '6'
        r = StaticInterface(label=label, domain=domain, ip_str=ip_str,
                            ip_type=ip_type, system=None)
        self.assertRaises(ValidationError, r.clean)
