from django.core.exceptions import ValidationError
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

    def test_invalid_field(self):
        test_csv = """
        hostname,warranty_start,warranty_end
        foobob.mozilla.com,2011-03-01,20192-03-12
        """.split('\n')
        self.assertRaises(ValueError, csv_import, test_csv, {'save': True})
        #s = System.objects.get(hostname='foobob.mozilla.com')
        #self.assertTrue(s.warranty_start)
        #self.assertTrue(s.warranty_end)

    def test_override(self):
        test_csv = """
        hostname,warranty_start,warranty_end
        foobob.mozilla.com,2011-03-01,2012-03-12
        """.split('\n')
        s = System.objects.create(hostname='foobob.mozilla.com', serial='1234')
        csv_import(test_csv, save=True)
        s = System.objects.get(hostname='foobob.mozilla.com')
        self.assertTrue(s.serial, '1234')

    def test_multiple_save(self):
        test_csv = """
        hostname
        foobob.mozilla.com
        foobob.mozilla.com
        """.split('\n')
        csv_import(test_csv, save=True)
        csv_import(test_csv, save=False)
        csv_import(test_csv, save=True)
        self.assertEqual(
            1, System.objects.filter(hostname='foobob.mozilla.com').count()
        )

    def test_invalid_mac(self):
        test_csv = """
        hostname,nic.0.mac_address.0
        foobob.mozilla.com,11:22:33:44:55:66:77
        """.split('\n')
        self.assertRaises(
            ValidationError, csv_import, test_csv, {'save': True}
        )

    def test_update_key_value(self):
        test_csv = """
        hostname,nic.0.name.0
        foobob.mozilla.com,nic0
        """.split('\n')
        csv_import(test_csv, save=True)
        s = System.objects.get(hostname='foobob.mozilla.com')
        self.assertEqual(1, s.keyvalue_set.filter(key='nic.0.name.0').count())
        self.assertEqual('nic0', s.keyvalue_set.get(key='nic.0.name.0').value)

        test_csv = """
        hostname,nic.0.name.0
        foobob.mozilla.com,nic33
        """.split('\n')
        csv_import(test_csv, save=True)
        s = System.objects.get(hostname='foobob.mozilla.com')
        self.assertEqual(1, s.keyvalue_set.filter(key='nic.0.name.0').count())
        self.assertEqual('nic33', s.keyvalue_set.get(key='nic.0.name.0').value)

        test_csv = """
        hostname,nic.0.mac_address.0
        foobob.mozilla.com,11:22:33:44:55:66
        """.split('\n')
        csv_import(test_csv, save=True)
        s = System.objects.get(hostname='foobob.mozilla.com')
        self.assertEqual(
            1, s.keyvalue_set.filter(key='nic.0.mac_address.0').count()
        )
        self.assertEqual(
            '11:22:33:44:55:66',
            s.keyvalue_set.get(key='nic.0.mac_address.0').value
        )
        test_csv = """
        hostname,nic.0.mac_address.0,nic.0.name.0
        foobob.mozilla.com,11:22:33:44:55:66,nic0
        """.split('\n')
        csv_import(test_csv, save=False)
        csv_import(test_csv, save=True)
        s = System.objects.get(hostname='foobob.mozilla.com')
        self.assertEqual(
            1, s.keyvalue_set.filter(key='nic.0.mac_address.0').count()
        )
        self.assertEqual(
            '11:22:33:44:55:66',
            s.keyvalue_set.get(key='nic.0.mac_address.0').value
        )
        self.assertEqual(1, s.keyvalue_set.filter(key='nic.0.name.0').count())
        self.assertEqual('nic0', s.keyvalue_set.get(key='nic.0.name.0').value)

    def test_get_asset_tag(self):
        test_csv = """
        hostname,warranty_start,warranty_end,asset_tag
        foobob.mozilla.com,2011-03-01,2012-03-12,1234
        """.split('\n')
        s = System.objects.create(hostname='foobob.mozilla.com')
        csv_import(test_csv, save=True)
        s = System.objects.get(hostname='foobob.mozilla.com')
        self.assertTrue(s.asset_tag, '1234')

        test_csv = """
        hostname,warranty_start,warranty_end,asset_tag
        changed-the-hostname.mozilla.com,2011-03-01,2012-03-12,1234
        """.split('\n')
        csv_import(test_csv, save=True, primary_attr='asset_tag')
        self.assertEqual(
            0, System.objects.filter(hostname='foobob.mozilla.com').count()
        )
        s = System.objects.get(hostname='changed-the-hostname.mozilla.com')
        self.assertTrue(s)
        self.assertEqual('1234', s.asset_tag)

    def test_two_primary_attribute(self):
        test_csv = """
        primary_attribute%hostname,primary_attribute%asset_tag
        foobob.mozilla.com,123
        """.split('\n')
        self.assertRaises(
            ValidationError, csv_import, test_csv, {'save': True}
        )

    def test_primary_attribute(self):
        s = System.objects.create(hostname='foobob.mozilla.com')
        test_csv = """
        primary_attribute%hostname,hostname
        foobob.mozilla.com,foobar.mozilla.com
        """.split('\n')
        csv_import(test_csv, save=True, primary_attr='asset_tag')
        # The primary_attr kwarg shouldn't affect anything

        s1 = System.objects.get(pk=s.pk)
        self.assertEqual('foobar.mozilla.com', s1.hostname)
