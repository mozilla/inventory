from django.test import TestCase
from mcsv.importer import csv_import
from systems.models import OperatingSystem, System


class CSVTests(TestCase):
    def setUp(self):
        OperatingSystem.objects.create(name='foo', version='1.1')
        OperatingSystem.objects.create(name='foo', version='2.1')
        OperatingSystem.objects.create(name='bar', version='2.1')

    def test_get_related(self):
        test_csv = """
        hostname,operating_system%name
        baz.mozilla.com,foo
        """.split('\n')
        self.assertRaises(Exception, csv_import, test_csv)

        test_csv = """
        hostname,operating_system%name
        baz.mozilla.com,foo%foo
        """.split('\n')
        self.assertRaises(Exception, csv_import, test_csv)

        test_csv = """
        hostname,operating_system
        baz.mozilla.com,foo%foo
        """.split('\n')
        self.assertRaises(Exception, csv_import, test_csv)

        test_csv = """
        hostname,operating_system%version
        baz.mozilla.com,foo%foo
        """.split('\n')
        self.assertRaises(Exception, csv_import, test_csv)

        test_csv = """
        hostname,operating_system%name%version
        foobob.mozilla.com,foo%1.1
        """.split('\n')
        ret = csv_import(test_csv)
        self.assertEqual(1, len(ret))
        self.assertTrue(ret[0]['system'])

    def test_multiple(self):
        test_csv = """
        hostname,operating_system%name%version
        foobob.mozilla.com,foo%1.1
        1fooboz.mozilla.com,foo%1.1
        2fooboz.mozilla.com,foo%1.1
        3fooboz.mozilla.com,foo%1.1
        4fooboz.mozilla.com,foo%1.1
        5fooboz.mozilla.com,foo%1.1
        6fooboz.mozilla.com,foo%1.1
        7fooboz.mozilla.com,foo%1.1
        8fooboz.mozilla.com,foo%1.1
        """.split('\n')
        before = System.objects.all().count()
        ret = csv_import(test_csv)
        after = System.objects.all().count()
        self.assertEqual(9, len(ret))
        self.assertEqual(before, after - 9)

    def test_multiple_no_save(self):
        test_csv = """
        hostname,operating_system%name%version
        foobob.mozilla.com,foo%1.1
        1fooboz.mozilla.com,foo%1.1
        2fooboz.mozilla.com,foo%1.1
        3fooboz.mozilla.com,foo%1.1
        4fooboz.mozilla.com,foo%1.1
        5fooboz.mozilla.com,foo%1.1
        6fooboz.mozilla.com,foo%1.1
        7fooboz.mozilla.com,foo%1.1
        8fooboz.mozilla.com,foo%1.1
        """.split('\n')
        before = System.objects.all().count()
        ret = csv_import(test_csv, save=False)
        after = System.objects.all().count()
        self.assertEqual(9, len(ret))
        self.assertEqual(before, after)

    def test_keyvalue(self):
        test_csv = """
        hostname,nic.0.mac_address.0
        foobob.mozilla.com,keyvalue
        """.split('\n')
        ret = csv_import(test_csv, save=False)
        self.assertTrue(ret[0]['kvs'])

    def test_warranty_start_end(self):
        test_csv = """
        hostname,warranty_start,warranty_end
        foobob.mozilla.com,2011-03-01,2012-03-12
        """.split('\n')
        csv_import(test_csv, save=True)
        s = System.objects.get(hostname='foobob.mozilla.com')
        self.assertTrue(s.warranty_start)
        self.assertTrue(s.warranty_end)
