from itertools import izip

from django.test import TestCase

from mozdns.tests.utils import create_fake_zone
from mozdns.ptr.models import PTR
from mozdns.cname.models import CNAME
from mozdns.address_record.models import AddressRecord
from core.search.compiler.django_compile import compile_q_objects
from core.search.compiler.invfilter import searchables


class SearchTests(TestCase):
    def searchables_to_map(self, qs):
        """A temporary function untill things can be rewritten."""
        self.assertEqual(len(qs), len(searchables))
        hmap = {}
        for q, (type_, Klass) in izip(qs, searchables):
            if q is None:
                hmap[type_] = []
            else:
                hmap[type_] = Klass.objects.filter(q)
        return hmap

    def search(self, search):
        """Because the interface is changing soon."""
        qs, errors = compile_q_objects(search)
        if errors:
            return None, errors
        return self.searchables_to_map(qs)

    def test_integration1(self):
        create_fake_zone("wee.wee.mozilla.com", "")
        res = self.search("wee.wee.mozilla.com")
        self.assertEqual(len(res['SOA']), 1)
        self.assertEqual(len(res['NS']), 1)
        self.assertEqual(len(res['DOMAIN']), 1)

        create_fake_zone("wee1.wee.mozilla.com", "")
        res = self.search("wee1.wee.mozilla.com")
        self.assertEqual(len(res['SOA']), 1)
        self.assertEqual(len(res['NS']), 1)
        self.assertEqual(len(res['DOMAIN']), 1)

        res = self.search("wee1.wee.mozilla.com OR wee.wee.mozilla.com")
        self.assertEqual(len(res['SOA']), 2)
        self.assertEqual(len(res['NS']), 2)
        self.assertEqual(len(res['DOMAIN']), 2)

        res = self.search("wee1.wee.mozilla.com type=:SOA")
        self.assertEqual(len(res['SOA']), 1)
        self.assertEqual(len(res['NS']), 0)
        self.assertEqual(len(res['DOMAIN']), 0)

        res = self.search(
            "wee1.wee.mozilla.com type=:NS OR "
            "wee.wee.mozilla.com type=:DOMAIN")
        self.assertEqual(len(res['SOA']), 0)
        self.assertEqual(len(res['NS']), 1)
        self.assertEqual(len(res['DOMAIN']), 1)

    def test_integration2(self):
        root_domain = create_fake_zone("wee2.wee.mozilla.com", "")
        res = self.search("wee2.wee.mozilla.com")
        self.assertEqual(len(res['SOA']), 1)
        self.assertEqual(len(res['NS']), 1)
        self.assertEqual(len(res['DOMAIN']), 1)

        create_fake_zone("1.1.ip6.arpa", "")
        res = self.search("1.1.ip6.arpa")
        self.assertEqual(len(res['SOA']), 1)
        self.assertEqual(len(res['NS']), 1)
        self.assertEqual(len(res['DOMAIN']), 1)

        ptr = PTR(name="host1.wee2.wee.mozilla.com", ip_str="1111::",
                  ip_type="6")
        ptr.save()
        addr = AddressRecord(label="host1", domain=root_domain, ip_str="11::",
                             ip_type="6")
        addr.save()
        res = self.search("host1.wee2.wee.mozilla.com")
        self.assertEqual(len(res['A']), 1)
        self.assertEqual(len(res['PTR']), 1)

        res = self.search("host1.wee2.wee.mozilla.com type=:A")
        self.assertEqual(len(res['A']), 1)
        self.assertEqual(len(res['PTR']), 0)

        res = self.search("host1.wee2.wee.mozilla.com type=:PTR")
        self.assertEqual(len(res['A']), 0)
        self.assertEqual(len(res['PTR']), 1)

        res = self.search("host1.wee2.wee.mozilla.com type=:A type=:PTR")
        self.assertEqual(len(res['A']), 0)
        self.assertEqual(len(res['PTR']), 0)

    def test_integration3_zone(self):
        root_domain = create_fake_zone("wee3.wee.mozilla.com", "")
        res = self.search("zone=:wee3.wee.mozilla.com")
        self.assertEqual(len(res['SOA']), 1)
        self.assertEqual(len(res['NS']), 1)
        cn = CNAME(label="host1", domain=root_domain, target="whop.whop")
        cn.save()
        res = self.search("zone=:wee3.wee.mozilla.com host1")
        self.assertEqual(len(res['SOA']), 0)
        self.assertEqual(len(res['NS']), 0)
        self.assertEqual(len(res['CNAME']), 1)

        res = self.search("zone=:wee3.wee.mozilla.com type=:CNAME")
        self.assertEqual(len(res['SOA']), 0)
        self.assertEqual(len(res['NS']), 0)
        self.assertEqual(len(res['CNAME']), 1)
