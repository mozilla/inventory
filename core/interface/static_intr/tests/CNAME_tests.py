from django.test import TestCase
from django.core.exceptions import ValidationError

from core.interface.static_intr.models import StaticInterface
from systems.models import System
from mozdns.domain.models import Domain
from mozdns.cname.models import CNAME
from mozdns.ptr.models import PTR

from mozdns.ip.utils import ip2dns_form, nibbilize

import pdb

class CNAMEStaticRegTests(TestCase):
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
        self.arpa = self.create_domain( name = 'arpa')
        self.arpa.save()
        self.i_arpa = self.create_domain( name = 'in-addr.arpa')
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

    def do_delete(self, r):
        ip_str = r.ip_str
        fqdn = r.fqdn
        r.delete()
        self.assertFalse(AddressRecord.objects.filter(ip_str=ip_str, fqdn=fqdn))

    def test1_delete_cname(self):
        mac = "11:22:33:44:55:66"
        label = "foo4"
        domain = self.f_c
        ip_str = "10.0.0.2"
        kwargs = {'mac':mac, 'label':label, 'domain':domain, 'ip_str':ip_str}
        i = self.do_add_intr(**kwargs)
        cn, _ = CNAME.objects.get_or_create(label='foo', domain=domain,
                data=label+"."+domain.name)
        self.assertRaises(ValidationError, i.delete)

    def test1_delete_override(self):
        mac = "12:22:33:44:55:66"
        label = "foo6"
        domain = self.f_c
        ip_str = "10.0.0.2"
        kwargs = {'mac':mac, 'label':label, 'domain':domain, 'ip_str':ip_str}
        i = self.do_add_intr(**kwargs)
        cn, _ = CNAME.objects.get_or_create(label='food', domain=domain,
                data=label+"."+domain.name)
        i.delete(check_cname=False)
