from django.test import TestCase
from django.core.exceptions import ValidationError

from core.registration.static.models import StaticReg
from systems.tests.utils import create_fake_host
from mozdns.domain.models import Domain
from mozdns.address_record.models import AddressRecord
from mozdns.ptr.models import PTR
from mozdns.view.models import View

from mozdns.ip.utils import ip_to_domain_name


class StaticRegTests(TestCase):
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
        self.i_arpa = self.create_domain(name='in-addr.arpa')
        self.i_arpa.save()

        self.c = Domain(name="ccc")
        self.c.save()
        self.f_c = Domain(name="foo.ccc")
        self.f_c.save()
        self.r1 = self.create_domain(name="10")
        self.r1.save()

        self.r2 = self.create_domain(name="128")
        self.r2.save()
        self.n = create_fake_host(hostname="foo.mozilla.com")
        self.n.clean()
        self.n.save()
        View.objects.get_or_create(name="private")

    def do_add(self, label, domain, ip_str, ip_type='4'):
        r = StaticReg(
            label=label, domain=domain, ip_str=ip_str, ip_type=ip_type,
            system=self.n
        )
        r.clean()
        r.save()
        r.details()
        r.get_edit_url()
        r.get_delete_url()
        r.get_absolute_url()
        repr(r)
        return r

    def do_delete(self, r):
        ip_str = r.ip_str
        fqdn = r.fqdn
        r.delete()
        self.assertFalse(
            AddressRecord.objects.filter(ip_str=ip_str, fqdn=fqdn)
        )

    def test1_create_basic(self):
        label = "foo"
        domain = self.f_c
        ip_str = "10.0.0.2"
        kwargs = {
            'label': label, 'domain': domain,
            'ip_str': ip_str
        }
        self.do_add(**kwargs)

    def test2_create_basic(self):
        label = "foo1"
        domain = self.f_c
        ip_str = "10.0.0.1"
        kwargs = {
            'label': label, 'domain': domain, 'ip_str': ip_str,
        }
        i = self.do_add(**kwargs)
        self.assertEqual(self.r1, i.reverse_domain)

        i2 = StaticReg.objects.get(pk=i.pk)
        self.assertEqual(self.r1, i2.reverse_domain)

    def test3_create_basic(self):
        label = "foo1"
        domain = self.f_c
        ip_str = "10.0.0.2"
        kwargs = {
            'label': label, 'domain': domain, 'ip_str': ip_str,
        }
        self.do_add(**kwargs)

    def test4_create_basic(self):
        label = "foo1"
        domain = self.f_c
        ip_str = "10.0.0.2"
        kwargs = {
            'label': label, 'domain': domain, 'ip_str': ip_str,
        }
        self.do_add(**kwargs)

    def test6_create_basic(self):
        label = "foo1"
        domain = self.f_c
        ip_str = "128.0.0.2"
        kwargs = {
            'label': label, 'domain': domain, 'ip_str': ip_str,
        }
        i = self.do_add(**kwargs)
        self.assertEqual(self.r2, i.reverse_domain)

    def test1_delete(self):
        label = "foo1"
        domain = self.f_c
        ip_str = "10.0.0.2"
        kwargs = {'label': label, 'domain': domain, 'ip_str': ip_str}
        r = self.do_add(**kwargs)
        self.do_delete(r)

    def test1_dup_create_basic(self):
        label = "foo3"
        domain = self.f_c
        ip_str = "10.0.0.2"
        kwargs = {
            'label': label, 'domain': domain, 'ip_str': ip_str,
        }
        self.do_add(**kwargs)
        self.assertRaises(ValidationError, self.do_add, **kwargs)

    def test1_bad_add_for_a_ptr(self):
        # sreg exists, then try ptr and A
        label = "9988food"
        domain = self.c
        ip_str = "10.0.0.1"
        kwargs = {
            'label': label, 'domain': domain, 'ip_str': ip_str,
        }
        ip_type = '4'
        i = self.do_add(**kwargs)
        i.clean()
        i.save()
        a = AddressRecord(label=label, domain=domain, ip_str=ip_str,
                          ip_type=ip_type)
        self.assertRaises(ValidationError, a.save)
        ptr = PTR(ip_str=ip_str, ip_type=ip_type, name=i.fqdn)
        self.assertRaises(ValidationError, ptr.save)

    def test2_bad_add_for_a_ptr(self):
        # PTR and A exist, then try add sreg
        label = "9988fdfood"
        domain = self.c
        ip_str = "10.0.0.1"
        kwargs = {
            'label': label, 'domain': domain, 'ip_str': ip_str,
        }
        ip_type = '4'
        a = AddressRecord.objects.create(
            label=label, domain=domain, ip_str=ip_str, ip_type=ip_type
        )
        PTR.objects.create(ip_str=ip_str, ip_type=ip_type, name=a.fqdn)
        self.assertRaises(ValidationError, self.do_add, **kwargs)

    def test1_bad_reverse_domain(self):
        label = "8888foo"
        domain = self.f_c
        ip_str = "10.0.0.1"
        kwargs = {
            'label': label, 'domain': domain, 'ip_str': ip_str,
        }
        i = self.do_add(**kwargs)
        i.ip_str = "9.0.0.1"
        self.assertRaises(ValidationError, i.save)

    def test1_no_system(self):
        label = "8888foo"
        domain = self.f_c
        ip_str = "10.0.0.1"
        ip_type = '4'
        r = StaticReg(
            label=label, domain=domain, ip_str=ip_str, ip_type=ip_type,
            system=None
        )
        self.assertRaises(ValidationError, r.save)
