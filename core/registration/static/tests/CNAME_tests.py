from django.test import TestCase
from django.core.exceptions import ValidationError

from core.registration.static.models import StaticReg
from systems.tests.utils import create_fake_host
from mozdns.domain.models import Domain
from mozdns.cname.models import CNAME

from mozdns.ip.utils import ip_to_domain_name


class CNAMEStaticRegTests(TestCase):
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

    def test1_delete_cname(self):
        label = "foo4"
        domain = self.f_c
        ip_str = "10.0.0.2"
        kwargs = {'label': label, 'domain': domain,
                  'ip_str': ip_str}
        i = self.do_add_sreg(**kwargs)
        cn, _ = CNAME.objects.get_or_create(label='foo', domain=domain,
                                            target=label + "." + domain.name)
        self.assertRaises(ValidationError, i.delete)

    def test1_delete_override(self):
        label = "foo6"
        domain = self.f_c
        ip_str = "10.0.0.2"
        kwargs = {'label': label, 'domain': domain,
                  'ip_str': ip_str}
        i = self.do_add_sreg(**kwargs)
        cn, _ = CNAME.objects.get_or_create(label='food', domain=domain,
                                            target=label + "." + domain.name)
        i.delete(check_cname=False)
