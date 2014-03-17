from django.test import TestCase
from django.core.exceptions import ValidationError

from mozdns.ip.utils import ip_to_domain_name
from mozdns.ip.models import Ip

from mozdns.domain.models import Domain, boot_strap_ipv6_reverse_domain

from mozdns.ptr.models import PTR


class PTRTests(TestCase):
    def setUp(self):
        self.arpa = self.create_domain(name='arpa')
        self.i_arpa = self.create_domain(name='in-addr.arpa')
        self.i6_arpa = self.create_domain(name='ip6.arpa')

        self._128 = self.create_domain(name='128', ip_type='4')
        self._128.save()
        boot_strap_ipv6_reverse_domain("8.6.2.0")
        self.osu_block = "8620:105:F000:"
        self.o, _ = Domain.objects.get_or_create(name="edu")
        self.o_e, _ = Domain.objects.get_or_create(name="oregonstate.edu")
        self.b_o_e, _ = Domain.objects.get_or_create(
            name="bar.oregonstate.edu")

    def create_domain(self, name, ip_type=None, delegated=False):
        if ip_type is None:
            ip_type = '4'
        if name in ('arpa', 'in-addr.arpa', 'ip6.arpa'):
            pass
        else:
            name = ip_to_domain_name(name, ip_type=ip_type)
        d, _ = Domain.objects.get_or_create(name=name, delegated=delegated)
        self.assertTrue(d.is_reverse)
        return d

    def do_generic_add(self, ip_str, fqdn, ip_type, domain=None):
        ret = PTR(name=fqdn, ip_str=ip_str, ip_type=ip_type)
        ret.full_clean()
        ret.save()

        self.assertTrue(ret.details())
        self.assertTrue(ret.get_absolute_url())
        self.assertTrue(ret.get_edit_url())
        self.assertTrue(ret.get_delete_url())

        ip = Ip(ip_str=ip_str, ip_type=ip_type)
        ip.clean_ip()
        ptr = PTR.objects.filter(
            name=fqdn, ip_upper=ip.ip_upper, ip_lower=ip.ip_lower)
        ptr.__repr__()
        self.assertTrue(ptr)
        ip_str = ip_str.lower()
        self.assertEqual(ptr[0].ip_str, ip_str)
        if domain:
            if ptr[0].name == "":
                self.assertEqual(fqdn, domain.name)
            else:
                self.assertEqual(fqdn, ptr[0].name + "." + domain.name)
        else:
            self.assertEqual(fqdn, ptr[0].name)
        return ret

    def test_dns_form_ipv4(self):
        ret = self.do_generic_add(
            "128.193.1.230", "foo.bar.oregonstate.edu", '4')
        self.assertEqual("230.1.193.128.in-addr.arpa.", ret.dns_name())

    def test_dns_form_ipv6(self):
        ret = self.do_generic_add("8620:105:F000::1",
                                  "foo.bar.oregonstate.edu", '6')
        self.assertEqual("1.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.f.5."
                         "0.1.0.0.2.6.8.ip6.arpa.", ret.dns_name())

    def do_generic_invalid_add(self, ip, fqdn, ip_type, exception,
                               domain=None):
        # LOL, looks like I didn't know about assertRaises!
        e = None
        try:
            self.do_generic_add(ip, fqdn, ip_type, domain)
        except exception, e:
            pass
        self.assertEqual(exception, type(e))

    def test_no_domain(self):
        test_ip = "244.123.123.123"
        name = "foo"
        self.do_generic_invalid_add(test_ip, name, '4', ValidationError)

    def test_add_invalid_name_ipv6_ptr(self):
        bad_name = "testyfoo.com"
        test_ip = self.osu_block + ":1"
        bad_name = "2134!@#$!@"
        self.do_generic_invalid_add(test_ip, bad_name, '6', ValidationError)
        bad_name = "asdflj..com"
        self.do_generic_invalid_add(test_ip, bad_name, '6', ValidationError)
        bad_name = "A" * 257
        self.do_generic_invalid_add(test_ip, bad_name, '6', ValidationError)

    """
    Is this test redundant?
    """
    def test_add_invalid_name_ipv4_ptr(self):
        bad_name = "testyfoo.com"
        test_ip = "128.123.123.123"
        bad_name = "2134!@#$!@"
        self.do_generic_invalid_add(test_ip, bad_name, '4', ValidationError)
        bad_name = "asdflj..com"
        self.do_generic_invalid_add(test_ip, bad_name, '4', ValidationError)
        bad_name = "A" * 257
        self.do_generic_invalid_add(test_ip, bad_name, '4', ValidationError)

    def test_add_invalid_ip_ipv6_ptr(self):
        test_name = "testyfoo.com"
        bad_ip = "123.123.123.123."
        self.do_generic_invalid_add(bad_ip, test_name, '6', ValidationError)
        bad_ip = "123:!23:!23:"
        self.do_generic_invalid_add(bad_ip, test_name, '6', ValidationError)
        bad_ip = ":::"
        self.do_generic_invalid_add(bad_ip, test_name, '6', ValidationError)
        bad_ip = None
        self.do_generic_invalid_add(bad_ip, test_name, '6', ValidationError)
        bad_ip = True
        self.do_generic_invalid_add(bad_ip, test_name, '6', ValidationError)
        bad_ip = False
        self.do_generic_invalid_add(bad_ip, test_name, '6', ValidationError)
        bad_ip = lambda x: x
        self.do_generic_invalid_add(bad_ip, test_name, '6', ValidationError)

        bad_ip = "8::9:9:1"
        self.do_generic_invalid_add(bad_ip, test_name, '6', ValidationError)
        bad_ip = "11:9:9::1"
        self.do_generic_invalid_add(bad_ip, test_name, '6', ValidationError)

        bad_ip = "8.9.9.1"
        self.do_generic_invalid_add(bad_ip, test_name, '6', ValidationError)
        bad_ip = "11.9.9.1"
        self.do_generic_invalid_add(bad_ip, test_name, '6', ValidationError)

        bad_ip = self.osu_block + ":233"
        self.do_generic_add(bad_ip, "foo.bar.oregonstate.edu", '6')
        self.do_generic_invalid_add(bad_ip, "foo.bar.oregonstate.edu",
                                    '6', ValidationError)
        self.do_generic_invalid_add(self.osu_block + ":0:0:0233",
                                    "foo.bar.oregonstate.edu",
                                    '6', ValidationError)

        self.do_generic_add(self.osu_block + ":dd",
                            "foo.bar.oregondfastate.com", '6')
        self.do_generic_invalid_add(self.osu_block + ":dd",
                                    "foo.bar.oregondfastate.com",
                                    '6', ValidationError)

    def test_add_invalid_ip_ipv4_ptr(self):
        test_name = "testyfoo.com"
        bad_ip = "123.123"
        self.do_generic_invalid_add(bad_ip, test_name, '4', ValidationError)
        bad_ip = "asdfasdf"
        self.do_generic_invalid_add(bad_ip, test_name, '4', ValidationError)
        bad_ip = 32141243
        self.do_generic_invalid_add(bad_ip, test_name, '4', ValidationError)
        bad_ip = "128.123.123.123.123"
        self.do_generic_invalid_add(bad_ip, test_name, '4', ValidationError)
        bad_ip = "...."
        self.do_generic_invalid_add(bad_ip, test_name, '4', ValidationError)
        bad_ip = "1234."
        self.do_generic_invalid_add(bad_ip, test_name, '4', ValidationError)
        bad_ip = None
        self.do_generic_invalid_add(bad_ip, test_name, '4', ValidationError)
        bad_ip = False
        self.do_generic_invalid_add(bad_ip, test_name, '4', ValidationError)
        bad_ip = True
        self.do_generic_invalid_add(bad_ip, test_name, '4', ValidationError)

        bad_ip = "8.9.9.1"
        self.do_generic_invalid_add(bad_ip, test_name, '4', ValidationError)
        bad_ip = "11.9.9.1"
        self.do_generic_invalid_add(bad_ip, test_name, '4', ValidationError)

        self.do_generic_add("128.193.1.1", "foo.bar.oregonstate.edu", '4')
        self.do_generic_invalid_add(
            "128.193.1.1", "foo.bar.oregonstate.edu", '4', ValidationError)

        self.do_generic_add("128.128.1.1", "foo.bar.oregondfastate.com", '4')
        self.do_generic_invalid_add(
            "128.128.1.1", "foo.bar.oregondfastate.com", '4', ValidationError)

    def do_generic_remove(self, ip, fqdn, ip_type):
        ptr = PTR(ip_str=ip, name=fqdn, ip_type=ip_type)
        ptr.full_clean()
        ptr.save()

        ptr.delete()

        ip = Ip(ip_str=ip, ip_type=ip_type)
        ip.clean_ip()
        ptr = PTR.objects.filter(
            name=fqdn, ip_upper=ip.ip_upper, ip_lower=ip.ip_lower)
        self.assertFalse(ptr)

    def test_remove_ipv4(self):
        ip = "128.255.233.244"
        fqdn = "asdf34foo.bar.oregonstate.edu"
        self.do_generic_remove(ip, fqdn, '4')
        ip = "128.255.11.13"
        fqdn = "fo124kfasdfko.bar.oregonstate.edu"
        self.do_generic_remove(ip, fqdn, '4')
        ip = "128.255.9.1"
        fqdn = "or1fdsaflkegonstate.edu"
        self.do_generic_remove(ip, fqdn, '4')
        ip = "128.255.1.7"
        fqdn = "12.bar.oregonstate.edu"
        self.do_generic_remove(ip, fqdn, '4')
        ip = "128.255.1.3"
        fqdn = "fcwoo.bar.oregonstate.edu"
        self.do_generic_remove(ip, fqdn, '4')
        ip = "128.255.1.2"
        fqdn = "asffad124jfasf-oregonstate.edu"
        self.do_generic_remove(ip, fqdn, '4')

    def test_remove_ipv6(self):
        ip = self.osu_block + ":1"
        fqdn = "asdf34foo.bar.oregonstate.edu"
        self.do_generic_remove(ip, fqdn, '6')
        ip = self.osu_block + ":2"
        fqdn = "fo124kfasdfko.bar.oregonstate.edu"
        self.do_generic_remove(ip, fqdn, '6')
        ip = self.osu_block + ":8"
        fqdn = "or1fdsaflkegonstate.edu"
        self.do_generic_remove(ip, fqdn, '6')
        ip = self.osu_block + ":8"
        fqdn = "12.bar.oregonstate.edu"
        self.do_generic_remove(ip, fqdn, '6')
        ip = self.osu_block + ":20"
        fqdn = "fcwoo.bar.oregonstate.edu"
        self.do_generic_remove(ip, fqdn, '6')
        ip = self.osu_block + ":ad"
        fqdn = "asffad124jfasf-oregonstate.edu"
        self.do_generic_remove(ip, fqdn, '6')

    def do_generic_update(self, ptr, new_fqdn, ip_type):
        ptr.name = new_fqdn
        ptr.full_clean()
        ptr.save()

        ptr = PTR.objects.filter(
            name=new_fqdn, ip_upper=ptr.ip_upper, ip_lower=ptr.ip_lower)
        self.assertTrue(ptr)
        self.assertEqual(new_fqdn, ptr[0].name)

    def test_update_ipv4(self):
        ptr = self.do_generic_add("128.193.1.1", "oregonstate.edu", '4')
        fqdn = "nothing.nothing.nothing"
        self.do_generic_update(ptr, fqdn, '4')
        fqdn = "google.edu"
        self.do_generic_update(ptr, fqdn, '4')
        fqdn = "asdfasfd.oregonstate.edu"
        self.do_generic_update(ptr, fqdn, '4')
        fqdn = "asdfasf.foo.oregonstate.edu"
        self.do_generic_update(ptr, fqdn, '4')
        fqdn = "edu"
        self.do_generic_update(ptr, fqdn, '4')

    def test_update_ipv6(self):
        ptr = self.do_generic_add(
            self.osu_block + ":1", "oregonstate.edu", '6')
        fqdn = "nothing.nothing.nothing"
        self.do_generic_update(ptr, fqdn, '6')
        fqdn = "google.edu"
        self.do_generic_update(ptr, fqdn, '6')
        fqdn = "asdfasfd.oregonstate.edu"
        self.do_generic_update(ptr, fqdn, '6')
        fqdn = "asdfasf.foo.oregonstate.edu"
        self.do_generic_update(ptr, fqdn, '6')
        fqdn = "edu"
        self.do_generic_update(ptr, fqdn, '6')

    def do_generic_invalid_update(self, ptr, fqdn, ip_type, exception):
        e = None
        try:
            self.do_generic_update(ptr, fqdn, ip_type)
        except exception, e:
            pass
        self.assertEqual(exception, type(e))

    def test_invalid_update_ipv4(self):
        ptr = self.do_generic_add("128.3.1.1", "oregonstate.edu", '4')
        ptr2 = self.do_generic_add("128.3.1.1", "foo.oregonstate.edu", '4')
        fqdn = "oregonstate.edu"
        self.do_generic_invalid_update(ptr2, fqdn, '4', ValidationError)
        fqdn = ".oregonstate.edu "
        self.do_generic_invalid_update(ptr, fqdn, '4', ValidationError)
        fqdn = "asfd..as"
        self.do_generic_invalid_update(ptr, fqdn, '4', ValidationError)
        fqdn = "%.s#.com"
        self.do_generic_invalid_update(ptr, fqdn, '4', ValidationError)

    def test_invalid_update_ipv6(self):
        ptr = self.do_generic_add(
            self.osu_block + ":aa", "oregonstate.edu", '6')
        ptr2 = self.do_generic_add(
            self.osu_block + ":aa", "foo.oregonstate.edu", '6')
        fqdn = "oregonstate.edu"
        self.do_generic_invalid_update(ptr2, fqdn, '6', ValidationError)
        fqdn = "asfd..as"
        self.do_generic_invalid_update(ptr, fqdn, '6', ValidationError)
        fqdn = "%.s#.com"
        self.do_generic_invalid_update(ptr, fqdn, '6', ValidationError)
