from django.test import TestCase

from mozdns.tests.utils import create_fake_zone
from mozdns.ptr.models import PTR
from mozdns.cname.models import CNAME
from mozdns.address_record.models import AddressRecord
from core.search.compiler.django_compile import compile_to_django


class SearchDNSTests(TestCase):
    def test_integration1(self):
        create_fake_zone("wee.wee.mozilla.com", "")
        res, error = compile_to_django("wee.wee.mozilla.com")
        self.assertFalse(error)
        self.assertEqual(len(res['SOA']), 1)
        self.assertEqual(len(res['NS']), 1)
        self.assertEqual(len(res['DOMAIN']), 1)

        create_fake_zone("wee1.wee.mozilla.com", "")
        res, error = compile_to_django("wee1.wee.mozilla.com")
        self.assertFalse(error)
        self.assertEqual(len(res['SOA']), 1)
        self.assertEqual(len(res['NS']), 1)
        self.assertEqual(len(res['DOMAIN']), 1)

        res, error = compile_to_django("wee1.wee.mozilla.com OR "
                                       "wee.wee.mozilla.com")
        self.assertFalse(error)
        self.assertEqual(len(res['SOA']), 2)
        self.assertEqual(len(res['NS']), 2)
        self.assertEqual(len(res['DOMAIN']), 2)

        res, error = compile_to_django("wee1.wee.mozilla.com type=:SOA")
        self.assertFalse(error)
        self.assertEqual(len(res['SOA']), 1)
        self.assertEqual(len(res['NS']), 0)
        self.assertEqual(len(res['DOMAIN']), 0)

        res, error = compile_to_django(
            "wee1.wee.mozilla.com type=:NS OR "
            "wee.wee.mozilla.com type=:DOMAIN")
        self.assertFalse(error)
        self.assertEqual(len(res['SOA']), 0)
        self.assertEqual(len(res['NS']), 1)
        self.assertEqual(len(res['DOMAIN']), 1)

    def test_integration2(self):
        root_domain = create_fake_zone("wee2.wee.mozilla.com", "")
        res, error = compile_to_django("wee2.wee.mozilla.com")
        self.assertFalse(error)
        self.assertEqual(len(res['SOA']), 1)
        self.assertEqual(len(res['NS']), 1)
        self.assertEqual(len(res['DOMAIN']), 1)

        create_fake_zone("1.1.ip6.arpa", "")
        res, error = compile_to_django("1.1.ip6.arpa")
        self.assertFalse(error)
        self.assertEqual(len(res['SOA']), 1)
        self.assertEqual(len(res['NS']), 1)
        self.assertEqual(len(res['DOMAIN']), 1)

        ptr = PTR(name="host1.wee2.wee.mozilla.com", ip_str="1111::",
                  ip_type="6")
        ptr.save()
        addr = AddressRecord(label="host1", domain=root_domain, ip_str="11::",
                             ip_type="6")
        addr.save()
        res, error = compile_to_django("host1.wee2.wee.mozilla.com")
        self.assertFalse(error)
        self.assertEqual(len(res['A']), 1)
        self.assertEqual(len(res['PTR']), 1)

        res, error = compile_to_django("host1.wee2.wee.mozilla.com type=:A")
        self.assertFalse(error)
        self.assertEqual(len(res['A']), 1)
        self.assertEqual(len(res['PTR']), 0)

        res, error = compile_to_django("host1.wee2.wee.mozilla.com type=:PTR")
        self.assertFalse(error)
        self.assertEqual(len(res['A']), 0)
        self.assertEqual(len(res['PTR']), 1)

        res, error = compile_to_django("host1.wee2.wee.mozilla.com type=:A "
                                       "type=:PTR")
        self.assertFalse(error)
        self.assertEqual(len(res['A']), 0)
        self.assertEqual(len(res['PTR']), 0)

    def test_integration3_zone(self):
        root_domain = create_fake_zone("wee3.wee.mozilla.com", "")
        res, error = compile_to_django("zone=:wee3.wee.mozilla.com")
        self.assertFalse(error)
        self.assertEqual(len(res['SOA']), 1)
        self.assertEqual(len(res['NS']), 1)
        cn = CNAME(label="host1", domain=root_domain, target="whop.whop")
        cn.save()
        res, error = compile_to_django("zone=:wee3.wee.mozilla.com host1")
        self.assertFalse(error)
        self.assertEqual(len(res['SOA']), 0)
        self.assertEqual(len(res['NS']), 0)
        self.assertEqual(len(res['CNAME']), 1)

        res, error = compile_to_django("zone=:wee3.wee.mozilla.com "
                                       "type=:CNAME")
        self.assertFalse(error)
        self.assertEqual(len(res['SOA']), 0)
        self.assertEqual(len(res['NS']), 0)
        self.assertEqual(len(res['CNAME']), 1)

    def test_integration4_ip_range(self):
        create_fake_zone("wee3.wee.mozilla.com", "")
        create_fake_zone("1.2.ip6.arpa", "")
        res, error = compile_to_django("1.2.ip6.arpa")
        self.assertFalse(error)
        self.assertEqual(len(res['SOA']), 1)
        self.assertEqual(len(res['NS']), 1)
        self.assertEqual(len(res['DOMAIN']), 1)

        ptr = PTR(name="host1.wee2.wee.mozilla.com", ip_str="2111:0::",
                  ip_type="6")
        ptr.save()

        res, error = compile_to_django(ptr.ip_str)
        self.assertFalse(error)
        self.assertEqual(len(res['PTR']), 1)
        self.assertEqual(len(res['A']), 0)

        res, error = compile_to_django("2111:0:0::")
        self.assertFalse(error)
        self.assertEqual(len(res['PTR']), 0)
        self.assertEqual(len(res['A']), 0)

        res, error = compile_to_django("ip=:2111:0:0::")
        self.assertFalse(error)
        self.assertEqual(len(res['PTR']), 1)
        self.assertEqual(len(res['A']), 0)

        res, error = compile_to_django("ip=:2111:1:0::")
        self.assertFalse(error)
        self.assertEqual(len(res['PTR']), 0)
        self.assertEqual(len(res['A']), 0)

    def test_integration5_ip(self):
        root_domain = create_fake_zone("wee5.wee.mozilla.com", "")
        create_fake_zone("10.in-addr.arpa", "")
        res, error = compile_to_django("10.in-addr.arpa OR "
                                       "wee5.wee.mozilla.com")
        self.assertFalse(error)
        self.assertEqual(len(res['SOA']), 2)
        self.assertEqual(len(res['NS']), 2)
        self.assertEqual(len(res['DOMAIN']), 2)
        ptr = PTR(name="host1.wee2.wee.mozilla.com", ip_str="10.0.0.1",
                  ip_type="4")
        ptr.save()
        addr = AddressRecord(label="host1", domain=root_domain,
                             ip_str="10.0.0.1", ip_type="4")
        addr.save()

        res, error = compile_to_django(ptr.ip_str)
        self.assertFalse(error)
        self.assertEqual(len(res['PTR']), 1)
        self.assertEqual(len(res['A']), 1)

        res, error = compile_to_django("10.0.0.2")
        self.assertFalse(error)
        self.assertEqual(len(res['PTR']), 0)
        self.assertEqual(len(res['A']), 0)

        res, error = compile_to_django("ip=:10.0.0.1")
        self.assertFalse(error)
        self.assertEqual(len(res['PTR']), 1)
        self.assertEqual(len(res['A']), 1)
