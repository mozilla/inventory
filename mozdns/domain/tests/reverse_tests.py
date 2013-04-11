from django.test import TestCase
from django.core.exceptions import ValidationError

from mozdns.ptr.models import PTR
from mozdns.tests.view_tests import random_label
from mozdns.ip.models import ipv6_to_longs
from mozdns.ip.utils import ip_to_domain_name, nibbilize
from mozdns.domain.models import Domain, boot_strap_ipv6_reverse_domain
from mozdns.soa.models import SOA

import ipaddr


class ReverseDomainTests(TestCase):

    # This function speeds things up due to legamoz code
    def add_ptr_ipv4(self, ip):
        ptr = PTR(name=random_label(), ip_str=ip, ip_type='4')
        ptr.full_clean()
        ptr.save()
        return ptr

    def add_ptr_ipv6(self, ip):
        ptr = PTR(name=random_label(), ip_str=ip, ip_type='6')
        ptr.full_clean()
        ptr.save()
        return ptr

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

        self.i6_arpa = self.create_domain(name='ip6.arpa')
        self.i6_arpa.save()

    # Reverse Domain test functions
    def test_soa_validators(self):
        m = self.create_domain(name='8')
        m.save()

        f_m = self.create_domain(name='8.2')
        f_m.save()

        n_f_m = self.create_domain(name='8.2.3')
        n_f_m.save()

        b_m = self.create_domain(name='8.3')
        b_m.save()

        s = SOA(primary="ns1.foo.com", contact="asdf", description="test")
        s.save()

        f_m.soa = s
        f_m.save()

        b_m.soa = s
        self.assertRaises(ValidationError, b_m.save)

        n_f_m = Domain.objects.get(pk=n_f_m.pk)  # Refresh object
        n_f_m.soa = s
        n_f_m.save()

        m.soa = s
        m.save()

        b_m = Domain.objects.get(pk=b_m.pk)  # Refresh object
        b_m.soa = s
        b_m.save()

        m.soa = None
        self.assertRaises(ValidationError, m.save)

        s2 = SOA(primary="ns1.foo.com", contact="asdf", description="test2")
        s2.save()

        m.soa = s2
        self.assertRaises(ValidationError, m.save)

    def test_2_soa_validators(self):
        s1, _ = SOA.objects.get_or_create(
            primary="ns1.foo.gaz", contact="hostmaster.foo",
            description="foo.gaz2")
        d, _ = Domain.objects.get_or_create(name="11.in-addr.arpa")
        d.soa = None
        d.save()
        d1, _ = Domain.objects.get_or_create(name="12.in-addr.arpa")
        d1.soa = s1
        d1.save()

    def test_3_soa_validators(self):
        s1, _ = SOA.objects.get_or_create(
            primary="ns1.foo2.gaz", contact="hostmaster.foo",
            description="foo.gaz2")

        d, _ = Domain.objects.get_or_create(name="gaz")
        d.soa = s1
        d.save()

        r, _ = Domain.objects.get_or_create(name='9.in-addr.arpa')
        r.soa = s1
        self.assertRaises(ValidationError, r.save)

    def test_remove_reverse_domain(self):
        self.create_domain(name='127', ip_type='4').save()
        rd1 = self.create_domain(name='127.193', ip_type='4')
        rd1.save()
        rd1.__repr__()
        rd1.__str__()
        rd2 = self.create_domain(name='127.193.8', ip_type='4')
        rd2.save()
        rd2.__repr__()
        rd2.__str__()
        ip1 = self.add_ptr_ipv4('127.193.8.1')
        self.assertEqual(ip1.reverse_domain, rd2)
        ip2 = self.add_ptr_ipv4('127.193.8.2')
        self.assertEqual(ip2.reverse_domain, rd2)
        ip3 = self.add_ptr_ipv4('127.193.8.3')
        self.assertEqual(ip3.reverse_domain, rd2)
        ip4 = self.add_ptr_ipv4('127.193.8.4')
        self.assertEqual(ip4.reverse_domain, rd2)
        rd2.delete()
        ptr1 = PTR.objects.filter(ip_lower=ipaddr.IPv4Address(
            '127.193.8.1').__int__(), ip_type='4')[0]
        self.assertEqual(ptr1.reverse_domain, rd1)
        ptr2 = PTR.objects.filter(ip_lower=ipaddr.IPv4Address(
            '127.193.8.2').__int__(), ip_type='4')[0]
        self.assertEqual(ptr2.reverse_domain, rd1)
        ptr3 = PTR.objects.filter(ip_lower=ipaddr.IPv4Address(
            '127.193.8.2').__int__(), ip_type='4')[0]
        self.assertEqual(ptr3.reverse_domain, rd1)
        ptr4 = PTR.objects.filter(ip_lower=ipaddr.IPv4Address(
            '127.193.8.3').__int__(), ip_type='4')[0]
        self.assertEqual(ptr4.reverse_domain, rd1)

    def do_generic_invalid_operation(self, data, exception, function):
        e = None
        try:
            function(**data)
        except exception, e:
            pass
        self.assertEqual(exception, type(e))

    def test_bad_nibble(self):
        bad_data = {'addr': "asdfas"}
        self.do_generic_invalid_operation(bad_data, ValidationError, nibbilize)
        bad_data = {'addr': 12341245}
        self.do_generic_invalid_operation(bad_data, ValidationError, nibbilize)
        bad_data = {'addr': "123.123.123.123"}
        self.do_generic_invalid_operation(bad_data, ValidationError, nibbilize)
        bad_data = {'addr': True}
        self.do_generic_invalid_operation(bad_data, ValidationError, nibbilize)
        bad_data = {'addr': False}
        self.do_generic_invalid_operation(bad_data, ValidationError, nibbilize)

    def test_remove_invalid_reverse_domain(self):
        rd1 = self.create_domain(name='130', ip_type='4')
        rd1.save()
        rd2 = self.create_domain(name='130.193', ip_type='4')
        rd2.save()
        rd3 = self.create_domain(name='130.193.8', ip_type='4')
        rd3.save()
        try:
            rd1.delete()
        except ValidationError, e:
            pass
        self.assertEqual(ValidationError, type(e))

    def test_master_domain(self):
        rd1 = self.create_domain(name='128', ip_type='4')
        rd1.save()
        rd2 = self.create_domain(name='128.193', ip_type='4')
        rd2.save()
        rd3 = self.create_domain(name='128.193.8', ip_type='4')
        rd3.save()
        self.assertEqual(rd3.master_domain, rd2)
        self.assertEqual(rd2.master_domain, rd1)
        self.assertEqual(rd1.master_domain, self.i_arpa)

    def test_add_reverse_domains(self):
        try:
            self.create_domain(name='192.168', ip_type='4').save()
        except ValidationError, e:
            pass
        self.assertEqual(ValidationError, type(e))
        e = None
        rdx = self.create_domain(name='192', ip_type='4')
        rdx.save()
        rdy = self.create_domain(name='192.168', ip_type='4')
        rdy.save()
        try:
            self.create_domain(name='192.168', ip_type='4').save()
        except ValidationError, e:
            pass
        self.assertEqual(ValidationError, type(e))
        e = None

        self.create_domain(name='128', ip_type='4').save()
        rd0 = self.create_domain(name='128.193', ip_type='4')
        rd0.save()
        ip1 = self.add_ptr_ipv4('128.193.8.1')
        self.assertEqual(ip1.reverse_domain, rd0)
        ip2 = self.add_ptr_ipv4('128.193.8.2')
        self.assertEqual(ip2.reverse_domain, rd0)
        ip3 = self.add_ptr_ipv4('128.193.8.3')
        self.assertEqual(ip3.reverse_domain, rd0)
        ip4 = self.add_ptr_ipv4('128.193.8.4')
        self.assertEqual(ip4.reverse_domain, rd0)
        rd1 = self.create_domain(name='128.193.8', ip_type='4')
        rd1.save()
        ptr1 = PTR.objects.filter(ip_lower=ipaddr.IPv4Address(
            '128.193.8.1').__int__(), ip_type='4')[0]
        self.assertEqual(ptr1.reverse_domain, rd1)
        ptr2 = PTR.objects.filter(ip_lower=ipaddr.IPv4Address(
            '128.193.8.2').__int__(), ip_type='4')[0]
        self.assertEqual(ptr2.reverse_domain, rd1)
        ptr3 = PTR.objects.filter(ip_lower=ipaddr.IPv4Address(
            '128.193.8.3').__int__(), ip_type='4')[0]
        self.assertEqual(ptr3.reverse_domain, rd1)
        ptr4 = PTR.objects.filter(ip_lower=ipaddr.IPv4Address(
            '128.193.8.4').__int__(), ip_type='4')[0]
        self.assertEqual(ptr4.reverse_domain, rd1)
        rd1.delete()
        ptr1 = PTR.objects.filter(ip_lower=ipaddr.IPv4Address(
            '128.193.8.1').__int__(), ip_type='4')[0]
        self.assertEqual(ptr1.reverse_domain, rd0)
        ptr2 = PTR.objects.filter(ip_lower=ipaddr.IPv4Address(
            '128.193.8.2').__int__(), ip_type='4')[0]
        self.assertEqual(ptr2.reverse_domain, rd0)
        ptr3 = PTR.objects.filter(ip_lower=ipaddr.IPv4Address(
            '128.193.8.2').__int__(), ip_type='4')[0]
        self.assertEqual(ptr3.reverse_domain, rd0)
        ptr4 = PTR.objects.filter(ip_lower=ipaddr.IPv4Address(
            '128.193.8.3').__int__(), ip_type='4')[0]
        self.assertEqual(ptr4.reverse_domain, rd0)

    def test_boot_strap_add_ipv6_domain(self):
        osu_block = "2.6.2.1.1.0.5.F.0.0.0"
        test_dname = osu_block + ".d.e.a.d.b.e.e.f"
        boot_strap_ipv6_reverse_domain(test_dname)
        try:
            self.create_domain(
                name='2.6.2.1.1.0.5.f.0.0.0', ip_type='6').save()
        except ValidationError, e:
            pass
        self.assertEqual(ValidationError, type(e))
        e = None
        try:
            self.create_domain(name='2.6.2.1', ip_type='6').save()
        except ValidationError, e:
            pass
        self.assertEqual(ValidationError, type(e))
        e = None
        try:
            self.create_domain(
                name='2.6.2.1.1.0.5.F.0.0.0.d.e.a.d', ip_type='6').save()
        except ValidationError, e:
            pass
        self.assertEqual(ValidationError, type(e))
        e = None
        try:
            self.create_domain(
                name='2.6.2.1.1.0.5.F.0.0.0.d.e.a.d.b.e.e.f',
                ip_type='6').save()
        except ValidationError, e:
            pass
        self.assertEqual(ValidationError, type(e))
        e = None
        try:
            self.create_domain(name=test_dname, ip_type='6').save()
        except ValidationError, e:
            pass
        self.assertEqual(ValidationError, type(e))
        e = None
        # These should pass
        boot_strap_ipv6_reverse_domain('7.6.2.4')
        boot_strap_ipv6_reverse_domain('6.6.2.5.1')
        # These are pretty unrealistic since they prodtrude into the host part
        # of the address.
        boot_strap_ipv6_reverse_domain(
            '4.6.2.2.1.0.5.3.f.0.0.0.1.2.3.4.1.2.3.4.1.2.3.4.1.2.3.4.1.2.3.4')
        boot_strap_ipv6_reverse_domain(
            '5.6.2.3.1.0.5.3.f.0.0.0.1.2.3.4.1.2.3.4.1.2.3.4')

    def test_add_reverse_domainless_ips(self):
        e = None
        try:
            self.add_ptr_ipv4('8.8.8.8')
        except ValidationError, e:
            pass
        self.assertEqual(ValidationError, type(e))
        e = None

        try:
            self.add_ptr_ipv6('2001:0db8:85a3:0000:0000:8a2e:0370:733')
        except ValidationError, e:
            pass
        self.assertEqual(ValidationError, type(e))
        e = None
        boot_strap_ipv6_reverse_domain("2.0.0.1")
        try:
            self.create_domain(name='2.0.0.1', ip_type='6').save()
        except ValidationError, e:
            pass
        self.assertEqual(ValidationError, type(e))
        e = None
        self.add_ptr_ipv6('2001:0db8:85a3:0000:0000:8a2e:0370:733')

    def test_ipv6_to_longs(self):
        ip = ipaddr.IPv6Address('2001:0db8:85a3:0000:0000:8a2e:0370:733')
        ret = ipv6_to_longs(ip.__str__())
        self.assertEqual(ret, (2306139570357600256, 151930230802227))

    def test_bad_names(self):
        name = None
        self.assertRaises(ValidationError, self.create_domain,
                          **{'name': name, 'ip_type': '6'})
        name = 124
        self.assertRaises(ValidationError, self.create_domain,
                          **{'name': name, 'ip_type': '6'})
        name = "0.9.0"
        ip_type = "asdf"
        self.assertRaises(ValidationError, self.create_domain,
                          **{'name': name, 'ip_type': ip_type})
        ip_type = None
        self.assertRaises(ValidationError, self.create_domain,
                          **{'name': name, 'ip_type': ip_type})
        ip_type = 1234
        self.assertRaises(ValidationError, self.create_domain,
                          **{'name': name, 'ip_type': ip_type})

    def test_add_remove_reverse_ipv6_domains(self):
        osu_block = "2620:105:F000"
        rd0 = boot_strap_ipv6_reverse_domain("2.6.2.0.0.1.0.5.f.0.0.0")

        ip1 = self.add_ptr_ipv6(osu_block + ":8000::1")
        self.assertEqual(ip1.reverse_domain, rd0)
        ip2 = self.add_ptr_ipv6(osu_block + ":8000::2")
        self.assertEqual(ip2.reverse_domain, rd0)
        ip3 = self.add_ptr_ipv6(osu_block + ":8000::3")
        self.assertEqual(ip3.reverse_domain, rd0)
        self.add_ptr_ipv6(osu_block + ":8000::4")

        rd1 = self.create_domain(name="2.6.2.0.0.1.0.5.f.0.0.0.8", ip_type='6')
        rd1.save()
        ip_upper, ip_lower = ipv6_to_longs(osu_block + ":8000::1")
        ptr1 = PTR.objects.filter(
            ip_upper=ip_upper, ip_lower=ip_lower, ip_type='6')[0]
        self.assertEqual(ptr1.reverse_domain, rd1)
        ip_upper, ip_lower = ipv6_to_longs(osu_block + ":8000::2")
        ptr2 = PTR.objects.filter(
            ip_upper=ip_upper, ip_lower=ip_lower, ip_type='6')[0]
        self.assertEqual(ptr2.reverse_domain, rd1)
        ip_upper, ip_lower = ipv6_to_longs(osu_block + ":8000::3")
        ptr3 = PTR.objects.filter(
            ip_upper=ip_upper, ip_lower=ip_lower, ip_type='6')[0]
        self.assertEqual(ptr3.reverse_domain, rd1)
        ip_upper, ip_lower = ipv6_to_longs(osu_block + ":8000::4")
        ptr4 = PTR.objects.filter(
            ip_upper=ip_upper, ip_lower=ip_lower, ip_type='6')[0]
        self.assertEqual(ptr4.reverse_domain, rd1)

        rd1.delete()

        ip_upper, ip_lower = ipv6_to_longs(osu_block + ":8000::1")
        ptr1 = PTR.objects.filter(
            ip_upper=ip_upper, ip_lower=ip_lower, ip_type='6')[0]
        self.assertEqual(ptr1.reverse_domain, rd0)
        ip_upper, ip_lower = ipv6_to_longs(osu_block + ":8000::2")
        ptr2 = PTR.objects.filter(
            ip_upper=ip_upper, ip_lower=ip_lower, ip_type='6')[0]
        self.assertEqual(ptr2.reverse_domain, rd0)
        ip_upper, ip_lower = ipv6_to_longs(osu_block + ":8000::3")
        ptr3 = PTR.objects.filter(
            ip_upper=ip_upper, ip_lower=ip_lower, ip_type='6')[0]
        self.assertEqual(ptr3.reverse_domain, rd0)
        ip_upper, ip_lower = ipv6_to_longs(osu_block + ":8000::4")
        ptr4 = PTR.objects.filter(
            ip_upper=ip_upper, ip_lower=ip_lower, ip_type='6')[0]
        self.assertEqual(ptr4.reverse_domain, rd0)

    def test_master_reverse_ipv6_domains(self):
        rds = []
        rd = self.create_domain(name='1', ip_type='6')
        rd.save()
        rds.append(rd)

        rd = self.create_domain(name='1.2', ip_type='6')
        rd.save()
        rds.append(rd)

        rd = self.create_domain(name='1.2.8', ip_type='6')
        rd.save()
        rds.append(rd)

        rd = self.create_domain(name='1.2.8.3', ip_type='6')
        rd.save()
        rds.append(rd)

        rd = self.create_domain(name='1.2.8.3.0', ip_type='6')
        rd.save()
        rds.append(rd)

        rd = self.create_domain(name='1.2.8.3.0.0', ip_type='6')
        rd.save()
        rds.append(rd)

        rd = self.create_domain(name='1.2.8.3.0.0.0', ip_type='6')
        rd.save()
        rds.append(rd)

        rd = self.create_domain(name='1.2.8.3.0.0.0.0', ip_type='6')
        rd.save()
        rds.append(rd)

        rd = self.create_domain(name='1.2.8.3.0.0.0.0.4', ip_type='6')
        rd.save()
        rds.append(rd)

        rd = self.create_domain(name='1.2.8.3.0.0.0.0.4.3', ip_type='6')
        rd.save()
        rds.append(rd)

        rd = self.create_domain(name='1.2.8.3.0.0.0.0.4.3.4', ip_type='6')
        rd.save()
        rds.append(rd)

        rd = self.create_domain(name='1.2.8.3.0.0.0.0.4.3.4.5', ip_type='6')
        rd.save()
        rds.append(rd)

        rd = self.create_domain(name='1.2.8.3.0.0.0.0.4.3.4.5.6', ip_type='6')
        rd.save()
        rds.append(rd)

        rd = self.create_domain(
            name='1.2.8.3.0.0.0.0.4.3.4.5.6.6', ip_type='6')
        rd.save()
        rds.append(rd)

        rd = self.create_domain(
            name='1.2.8.3.0.0.0.0.4.3.4.5.6.6.5', ip_type='6')
        rd.save()
        rds.append(rd)

        rd = self.create_domain(
            name='1.2.8.3.0.0.0.0.4.3.4.5.6.6.5.6', ip_type='6')
        rd.save()
        rds.append(rd)

        rd = self.create_domain(
            name='1.2.8.3.0.0.0.0.4.3.4.5.6.6.5.6.7', ip_type='6')
        rd.save()
        rds.append(rd)

        rd = self.create_domain(
            name='1.2.8.3.0.0.0.0.4.3.4.5.6.6.5.6.7.0', ip_type='6')
        rd.save()
        rds.append(rd)

        rd = self.create_domain(
            name='1.2.8.3.0.0.0.0.4.3.4.5.6.6.5.6.7.0.0', ip_type='6')
        rd.save()
        rds.append(rd)

        rd = self.create_domain(
            name='1.2.8.3.0.0.0.0.4.3.4.5.6.6.5.6.7.0.0.0', ip_type='6')
        rd.save()
        rds.append(rd)

        rd = self.create_domain(
            name='1.2.8.3.0.0.0.0.4.3.4.5.6.6.5.6.7.0.0.0.0', ip_type='6')
        rd.save()
        rds.append(rd)

        rd = self.create_domain(
            name='1.2.8.3.0.0.0.0.4.3.4.5.6.6.5.6.7.0.0.0.0.0', ip_type='6')
        rd.save()
        rds.append(rd)

        rd = self.create_domain(
            name='1.2.8.3.0.0.0.0.4.3.4.5.6.6.5.6.7.0.0.0.0.0.0', ip_type='6')
        rd.save()
        rds.append(rd)

        rd = self.create_domain(name='1.2.8.3.0.0.0.0.4.3.4.5.6.6.5.6.7.0.0.0'
                                '.0.0.0.0', ip_type='6')
        rd.save()
        rds.append(rd)

        rd = self.create_domain(name='1.2.8.3.0.0.0.0.4.3.4.5.6.6.5.6.7.0.0.0'
                                '.0.0.0.0.0', ip_type='6')
        rd.save()
        rds.append(rd)

        rd = self.create_domain(name='1.2.8.3.0.0.0.0.4.3.4.5.6.6.5.6.7.0.0.0'
                                '.0.0.0.0.0.0', ip_type='6')
        rd.save()
        rds.append(rd)

        rd = self.create_domain(name='1.2.8.3.0.0.0.0.4.3.4.5.6.6.5.6.7.0.0.0'
                                '.0.0.0.0.0.0.0', ip_type='6')
        rd.save()
        rds.append(rd)

        rd = self.create_domain(name='1.2.8.3.0.0.0.0.4.3.4.5.6.6.5.6.7.0.0.0'
                                '.0.0.0.0.0.0.0.0', ip_type='6')
        rd.save()
        rds.append(rd)

        rd = self.create_domain(name='1.2.8.3.0.0.0.0.4.3.4.5.6.6.5.6.7.0.0.0'
                                '.0.0.0.0.0.0.0.0.0', ip_type='6')
        rd.save()
        rds.append(rd)

        rd = self.create_domain(name='1.2.8.3.0.0.0.0.4.3.4.5.6.6.5.6.7.0.0.0'
                                '.0.0.0.0.0.0.0.0.0.3', ip_type='6')
        rd.save()
        rds.append(rd)

        rd = self.create_domain(name='1.2.8.3.0.0.0.0.4.3.4.5.6.6.5.6.7.0.0.0'
                                '.0.0.0.0.0.0.0.0.0.3.2', ip_type='6')
        rd.save()
        rds.append(rd)

        rd = self.create_domain(name='1.2.8.3.0.0.0.0.4.3.4.5.6.6.5.6.7.0.0.0'
                                '.0.0.0.0.0.0.0.0.0.3.2.1', ip_type='6')
        rd.save()
        rds.append(rd)

        for rd in list(enumerate(rds)):
            if rd[0] == 0:
                self.assertEqual(rd[1].master_domain, self.i6_arpa)
            else:
                self.assertEqual(rd[1].master_domain, rds[rd[0] - 1])
            self.assertTrue(rd[1].get_absolute_url())
            self.assertTrue(rd[1].get_edit_url())
            self.assertTrue(rd[1].get_delete_url())

        try:
            Domain.objects.filter(
                name=ip_to_domain_name('1.2.8.3.0.0.0.0.4.3.4.5.6.6.5.6.7.0.0',
                                       ip_type='6'))[0].delete()
        except ValidationError, e:
            pass
        self.assertEqual(ValidationError, type(e))

    def test_delegation_add_domain(self):
        dom = self.create_domain(name='3', delegated=True)
        dom.save()

        self.assertRaises(ValidationError, self.create_domain,
                          **{'name': '3.4', 'delegated': False})
