from django.test import TestCase

from core.registration.static.models import StaticReg
from core.registration.static.models import StaticRegKeyValue
from systems.tests.utils import create_fake_host
from mozdns.domain.models import Domain
from mozdns.address_record.models import AddressRecord

from mozdns.ip.utils import ip_to_domain_name


class AuxAttrTests(TestCase):
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

    def do_add(self, label, domain, ip_str, ip_type='4'):
        r = StaticReg.objects.create(
            label=label, domain=domain, ip_str=ip_str,
            ip_type=ip_type, system=self.n
        )
        repr(r)
        return r

    def do_delete(self, r):
        ip_str = r.ip_str
        fqdn = r.fqdn
        r.delete()
        self.assertFalse(
            AddressRecord.objects.filter(ip_str=ip_str, fqdn=fqdn))

    def test1_create(self):
        label = "foo"
        domain = self.f_c
        ip_str = "10.0.0.2"
        kwargs = {'label': label, 'domain': domain, 'ip_str': ip_str}
        sreg = self.do_add(**kwargs)
        sreg.update_attrs()

        def bad_get():
            sreg.attrs.primary
        self.assertRaises(AttributeError, bad_get)
        x = StaticRegKeyValue.objects.filter(key='primary', obj=sreg)
        self.assertFalse(x)
        sreg.attrs.primary = '1'
        self.assertEqual(sreg.attrs.cache['primary'], '1')
        self.assertEqual(sreg.attrs.primary, '1')
        x = StaticRegKeyValue.objects.filter(key='primary', obj=sreg)
        self.assertEqual(x[0].value, '1')

    def test6_create(self):
        label = "foo"
        domain = self.f_c
        ip_str = "10.0.0.2"
        kwargs = {'label': label, 'domain': domain, 'ip_str': ip_str}
        sreg = self.do_add(**kwargs)
        sreg.update_attrs()
        sreg.update_attrs()
        sreg.update_attrs()

        def bad_get():
            sreg.attrs.primary
        self.assertRaises(AttributeError, bad_get)
        sreg.attrs.primary = '1'
        self.assertEqual(sreg.attrs.primary, '1')
        self.assertEqual(sreg.attrs.cache['primary'], '1')

    def test2_create(self):
        label = "foo"
        domain = self.f_c
        ip_str = "10.0.0.2"
        kwargs = {'label': label, 'domain': domain, 'ip_str': ip_str}
        sreg = self.do_add(**kwargs)
        sreg.update_attrs()
        sreg.attrs.primary = '2'
        self.assertEqual(sreg.attrs.primary, '2')
        self.assertEqual(sreg.attrs.cache['primary'], '2')
        del sreg.attrs.primary

        def bad_get():
            sreg.attrs.primary
        self.assertRaises(AttributeError, bad_get)
        sreg.attrs.primary = '3'
        self.assertEqual(sreg.attrs.primary, '3')
        self.assertEqual(sreg.attrs.cache['primary'], '3')

    def test1_del(self):
        label = "foo"
        domain = self.f_c
        ip_str = "10.0.0.2"
        kwargs = {'label': label, 'domain': domain, 'ip_str': ip_str}
        sreg = self.do_add(**kwargs)
        sreg.update_attrs()
        sreg.attrs.primary = '88'
        self.assertEqual(sreg.attrs.primary, '88')
        del sreg.attrs.primary

        def bad_get():
            sreg.attrs.primary
        self.assertRaises(AttributeError, bad_get)

    def test3_create(self):
        label = "foo"
        domain = self.f_c
        ip_str = "10.0.0.2"
        kwargs = {'label': label, 'domain': domain, 'ip_str': ip_str}
        sreg = self.do_add(**kwargs)
        sreg.update_attrs()

    def test1_existing_attrs(self):
        label = "foo"
        domain = self.f_c
        ip_str = "10.0.0.2"
        kwargs = {'label': label, 'domain': domain, 'ip_str': ip_str}
        sreg = self.do_add(**kwargs)
        StaticRegKeyValue(key="foo", value="bar", obj=sreg).save()
        StaticRegKeyValue(
            key="interface_type", value="eth0", obj=sreg).save()
        StaticRegKeyValue(key="alias", value="5", obj=sreg).save()
        sreg.update_attrs()
        self.assertEqual(sreg.attrs.alias, '5')
        self.assertEqual(sreg.attrs.cache['alias'], '5')
        self.assertEqual(sreg.attrs.interface_type, 'eth0')
        self.assertEqual(sreg.attrs.cache['interface_type'], 'eth0')
        self.assertEqual(sreg.attrs.foo, 'bar')
        self.assertEqual(sreg.attrs.cache['foo'], 'bar')
