from django.test import TestCase
from django.core.exceptions import ValidationError

from core.registration.static.models import StaticReg
from systems.tests.utils import create_fake_host
from mozdns.domain.models import Domain
from mozdns.address_record.models import AddressRecord

from mozdns.ip.utils import ip_to_domain_name


class AStaticRegTests(TestCase):
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
        Domain.objects.all().delete()
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
        self.n = create_fake_host(hostname="foo.mozilla.com")
        self.n.clean()
        self.n.save()

    def do_add_sreg(self, label, domain, ip_str, ip_type='4'):
        r = StaticReg(
            label=label, domain=domain, ip_str=ip_str,
            ip_type=ip_type, system=self.n
        )
        r.clean()
        r.save()
        repr(r)
        return r

    def do_add_a(self, label, domain, ip_str, ip_type='4'):
        a = AddressRecord(label=label, domain=domain, ip_str=ip_str,
                          ip_type=ip_type)
        a.clean()
        a.save()
        return a

    def do_delete(self, r):
        ip_str = r.ip_str
        fqdn = r.fqdn
        r.delete()
        self.assertFalse(
            AddressRecord.objects.filter(ip_str=ip_str, fqdn=fqdn))

    def test1_conflict_add_sreg_first(self):
        # Add an sreg and make sure A can't exist.
        label = "foo4"
        domain = self.f_c
        ip_str = "10.0.0.2"
        kwargs = {'label': label, 'domain': domain, 'ip_str': ip_str}
        self.do_add_sreg(**kwargs)
        kwargs = {'label': label, 'domain': domain, 'ip_str': ip_str}
        self.assertRaises(ValidationError, self.do_add_a, **kwargs)

    def test1_conflict_add_A_first(self):
        # Add an A and make sure an sreg can't exist.
        label = "foo5"
        domain = self.f_c
        ip_str = "10.0.0.2"
        kwargs = {'label': label, 'domain': domain, 'ip_str': ip_str}
        self.do_add_a(**kwargs)
        kwargs = {'label': label, 'domain': domain, 'ip_str': ip_str}
        self.assertRaises(ValidationError, self.do_add_sreg, **kwargs)

    def test2_conflict_add_sreg_first(self):
        # Add an sreg and update an existing A to conflict. Test for exception.
        label = "fo99"
        domain = self.f_c
        ip_str = "10.0.0.2"
        kwargs = {'label': label, 'domain': domain, 'ip_str': ip_str}
        self.do_add_sreg(**kwargs)
        ip_str = "10.0.0.3"
        kwargs = {'label': label, 'domain': domain, 'ip_str': ip_str}
        a = self.do_add_a(**kwargs)
        a.ip_str = "10.0.0.2"
        self.assertRaises(ValidationError, a.save)

    def test2_conflict_add_A_first(self):
        # Add an A and update and existing sreg to conflict. Test for
        # exception.
        label = "foo98"
        domain = self.f_c
        ip_str = "10.0.0.2"
        # Add A
        kwargs = {'label': label, 'domain': domain, 'ip_str': ip_str}
        self.do_add_a(**kwargs)

        # Add StaticReg with diff IP
        ip_str = "10.0.0.3"
        kwargs = {'label': label, 'domain': domain, 'ip_str': ip_str}
        sreg = self.do_add_sreg(**kwargs)

        # Conflict the IP on the sreg
        sreg.ip_str = "10.0.0.2"
        self.assertRaises(ValidationError, sreg.save)
