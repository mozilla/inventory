from django.test import TestCase

from core.registration.static.models import StaticReg
from systems.tests.utils import create_fake_host
from mozdns.domain.models import Domain
from mozdns.address_record.models import AddressRecord
from mozdns.view.models import View

from mozdns.ip.utils import ip_to_domain_name


class DeleteStaticStaticRegTests(TestCase):
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
        self.n = create_fake_host(hostname="foo.mozilla.com")
        self.n.clean()
        self.n.save()
        View.objects.get_or_create(name="private")

    def do_add(self, label, domain, ip_str, system, ip_type='4'):
        r = StaticReg(
            label=label, domain=domain, ip_str=ip_str,
            ip_type=ip_type, system=system
        )
        r.clean()
        r.save()
        return r

    def do_delete(self, r):
        ip_str = r.ip_str
        fqdn = r.fqdn
        r.delete()
        self.assertFalse(
            AddressRecord.objects.filter(ip_str=ip_str, fqdn=fqdn))

    def test1_delete_basic(self):
        # Does deleting a system delete it's interfaces?
        label = "foo"
        domain = self.f_c
        ip_str = "10.0.0.2"
        system = create_fake_host(hostname="foo")
        system.save()
        kwargs = {
            'label': label, 'domain': domain, 'ip_str': ip_str,
            'system': system}
        self.do_add(**kwargs)
        self.assertTrue(StaticReg.objects.filter(**kwargs))
        system.delete()
        self.assertFalse(StaticReg.objects.filter(**kwargs))
