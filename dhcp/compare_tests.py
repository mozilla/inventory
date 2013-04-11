from django.test import TestCase
from django.test.client import Client
import json
from dhcp.DHCPHash import DHCPHash, compare_lists, DHCPHashCompare

class DHCPMigrateTest(TestCase):
    fixtures = ['testdata.json']

    def setUp(self):
        self.new_file = """
    host foofake1.db.phx1.mozilla.com {
        hardware ethernet AA:BB:46:83:BA:F0;
        fixed-address 10.99.99.11;
        filename "foo.bar.tar.gz";
        option host-name "foofake1.db.phx1.mozilla.com";
        option domain-name-servers "10.0.0.1,10.0.0.2";
        option domain-name "mozilla.com";
    }

    host foofake1.db.phx1.mozilla.com {
        hardware ethernet AA:BB:46:83:BA:F4;
        fixed-address 10.99.99.11;
    }

    host foofake2.db.phx1.mozilla.com {
        hardware ethernet AA:BB:05:72:18:38;
        fixed-address 10.99.99.12;
    }"""
        self.client = Client()

    def test1_hash_string_accepted(self):
        d = DHCPHash(self.new_file)
        self.assertEqual(d.list_string, self.new_file)

    """def test2_remove_formatting(self):
        d = DHCPHash(self.new_file)
        unformatted_string = "host foofake1.db.phx1.mozilla.com-asdfasdfasdfdsfa"
        unformatted_string += ' {hardware ethernet AA:BB:46:83:BA:F0;fixed-address 10.99.99.11;}\n'
        unformatted_string += 'host foofake1.db.phx1.mozilla.com-asdfadsf {hardware ethernet AA:BB:46:83:BA:F4;fixed-address 10.99.99.11;}\n'
        unformatted_string += 'host foofake2.db.phx1.mozilla.com-asdfasdf {hardware ethernet AA:BB:05:72:18:38;fixed-address 10.99.99.12;}\n'
        unformatted = d.remove_formatting(d.list_string)"""

    def test3_test_split(self):
        d = DHCPHash(self.new_file)
        unformatted = d.remove_formatting(d.list_string)
        the_list = d.split_lines(unformatted)
        self.assertEqual(len(the_list), 3)

    def test4_create_hash(self):
        d = DHCPHash(self.new_file)
        unformatted = d.remove_formatting(d.list_string)
        the_list = d.split_lines(unformatted)
        hashed_list = d.hash_list(the_list)
        self.assertEqual(hashed_list[0]['host'], 'foofake1.db.phx1.mozilla.com')
        self.assertEqual(hashed_list[0]['hardware ethernet'], 'AA:BB:46:83:BA:F0')
        self.assertEqual(hashed_list[0]['fixed-address'], '10.99.99.11')
        self.assertEqual(hashed_list[0]['option domain-name'], 'mozilla.com')
        self.assertEqual(hashed_list[0]['option host-name'], 'foofake1.db.phx1.mozilla.com')
        self.assertEqual(hashed_list[0]['option domain-name-servers'], '10.0.0.1,10.0.0.2')


    def test5_host_missing_from_one_list(self):
        d = DHCPHash(self.new_file)
        unformatted = d.remove_formatting(d.list_string)
        the_list = d.split_lines(unformatted)
        hashed_list = d.hash_list(the_list)
        second_hash = list(hashed_list)
        self.assertEqual(hashed_list, second_hash)
        second_hash.pop()
        self.assertNotEqual(hashed_list, second_hash)
        resp = compare_lists(hashed_list, second_hash)
        self.assertNotEqual(resp, None)

    def test6_host_different_from_one_list(self):
        a = DHCPHash(self.new_file)
        b = DHCPHash(self.new_file)
        a_hashed_list = a.get_hash()
        b_hashed_list = b.get_hash()
        self.assertEqual(a_hashed_list, b_hashed_list)
        self.assertEqual(compare_lists(a_hashed_list, b_hashed_list), None)
        self.assertNotEqual(id(a_hashed_list), id(b_hashed_list))
        a_hashed_list[0]['host'] = 'im.fake.yep'
        self.assertNotEqual(compare_lists(a_hashed_list, b_hashed_list), None)

    def test7_hardware_ethernet_different_from_one_list(self):
        a = DHCPHash(self.new_file)
        b = DHCPHash(self.new_file)
        a_hashed_list = a.get_hash()
        b_hashed_list = b.get_hash()
        self.assertEqual(a_hashed_list, b_hashed_list)
        self.assertEqual(compare_lists(a_hashed_list, b_hashed_list), None)
        self.assertNotEqual(id(a_hashed_list), id(b_hashed_list))
        a_hashed_list[0]['hardware ethernet'] = '00:00:00:AA:BB:AB'
        self.assertNotEqual(compare_lists(a_hashed_list, b_hashed_list), None)

    def test8_extra_option_in_one_list_different_from_one_list(self):
        a = DHCPHash(self.new_file)
        b = DHCPHash(self.new_file)
        a_hashed_list = a.get_hash()
        b_hashed_list = b.get_hash()

        self.assertEqual(a_hashed_list, b_hashed_list)
        self.assertEqual(compare_lists(a_hashed_list, b_hashed_list), None)
        self.assertNotEqual(id(a_hashed_list), id(b_hashed_list))
        a_hashed_list[1]['filename'] = 'asdfasfdasdf.tar.gz'
        self.assertNotEqual(compare_lists(a_hashed_list, b_hashed_list), None)

    def test9_initial_dhcp_hash_compare(self):
        a = DHCPHash(self.new_file)
        b = DHCPHash(self.new_file)
        a_hashed_list = a.get_hash()
        b_hashed_list = b.get_hash()
        dc = DHCPHashCompare(a_hashed_list, 'KeyValue List', b_hashed_list, 'StaticINTR Generated')
        identical, lists = dc.compare_lists(a_hashed_list, b_hashed_list)
        self.assertTrue(identical)
        self.assertEqual(lists[0], lists[1])

    def test10_initial_dhcp_hash_compare_missing_host(self):
        a = DHCPHash(self.new_file)
        b = DHCPHash(self.new_file)
        a_hashed_list = a.get_hash()
        b_hashed_list = b.get_hash()

        del a_hashed_list[1]
        del b_hashed_list[1]
        del a_hashed_list[1]
        ## Pick the first object from the hash and give it a new and different value
        a_hashed_list[0]['hardware ethernet'] = '00:00:00:00:00:00'
        a_hashed_list[0]['fixed-address'] = '10.0.0.1'
        dc = DHCPHashCompare(a_hashed_list, 'KeyValue List', b_hashed_list, 'StaticINTR Generated')
        identical, lists = dc.compare_lists(a_hashed_list, b_hashed_list)
        self.assertFalse(identical)
        msg = dc.analyze()
        print msg
