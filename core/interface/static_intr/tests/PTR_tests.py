from django.test import TestCase
from django.core.exceptions import ValidationError

from core.interface.static_intr.models import StaticInterface
from systems.models import System
from mozdns.domain.models import Domain
from mozdns.ptr.models import PTR

from mozdns.ip.utils import ip_to_domain_name


class PTRStaticRegTests(TestCase):
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
        self.n = System()
        self.n.clean()
        self.n.save()

    def do_add_intr(self, mac, label, domain, ip_str, ip_type='4'):
        r = StaticInterface(mac=mac, label=label, domain=domain, ip_str=ip_str,
                            ip_type=ip_type, system=self.n)
        r.clean()
        r.save()
        repr(r)
        return r

    def do_add_ptr(self, label, domain, ip_str, ip_type='4'):
        ptr = PTR(name=label + '.' + domain.name, ip_str=ip_str,
                  ip_type=ip_type)
        ptr.clean()
        ptr.save()
        return ptr

    def test1_conflict_add_intr_first(self):
        # PTRdd an intr and make sure PTR can't exist.
        mac = "11:22:33:44:55:66"
        label = "foo4"
        domain = self.f_c
        ip_str = "10.0.0.2"
        kwargs = {'mac': mac, 'label': label, 'domain': domain,
                  'ip_str': ip_str}
        self.do_add_intr(**kwargs)
        kwargs = {'label': label, 'domain': domain, 'ip_str': ip_str}
        self.assertRaises(ValidationError, self.do_add_ptr, **kwargs)

    def test1_conflict_add_PTR_first(self):
        # Add an PTR and make sure an intr can't exist.
        mac = "11:22:33:44:55:66"
        label = "foo5"
        domain = self.f_c
        ip_str = "10.0.0.2"
        kwargs = {'label': label, 'domain': domain, 'ip_str': ip_str}
        self.do_add_ptr(**kwargs)
        kwargs = {'mac': mac, 'label': label, 'domain': domain,
                  'ip_str': ip_str}
        self.assertRaises(ValidationError, self.do_add_intr, **kwargs)

    def test2_conflict_add_intr_first(self):
        # Add an intr and update an existing PTR to conflict. Test for
        # exception.
        mac = "12:22:33:44:55:66"
        label = "fo99"
        domain = self.f_c
        ip_str = "10.0.0.2"
        kwargs = {'mac': mac, 'label': label, 'domain': domain,
                  'ip_str': ip_str}
        self.do_add_intr(**kwargs)
        ip_str = "10.0.0.3"
        kwargs = {'label': label, 'domain': domain, 'ip_str': ip_str}
        ptr = self.do_add_ptr(**kwargs)
        ptr.ip_str = "10.0.0.2"
        self.assertRaises(ValidationError, ptr.clean)

    def test2_conflict_add_A_first(self):
        # Add an PTR and update and existing intr to conflict. Test for
        # exception.
        mac = "11:22:33:44:55:66"
        label = "foo98"
        domain = self.f_c
        ip_str = "10.0.0.2"
        # Add PTR
        kwargs = {'label': label, 'domain': domain, 'ip_str': ip_str}
        self.do_add_ptr(**kwargs)

        # Add Intr with diff IP
        ip_str = "10.0.0.3"
        kwargs = {'mac': mac, 'label': label, 'domain': domain,
                  'ip_str': ip_str}
        intr = self.do_add_intr(**kwargs)

        # Conflict the IP on the intr
        intr.ip_str = "10.0.0.2"
        self.assertRaises(ValidationError, intr.save)
