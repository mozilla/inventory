from django.core.exceptions import ValidationError
from django.test import TestCase, Client

from mcsv.importer import csv_import
from systems.models import (
    OperatingSystem, System, SystemRack, Allocation, Location, SystemStatus
)

import datetime


class CSVTests(TestCase):
    def setUp(self):
        OperatingSystem.objects.create(name='foo', version='1.1')
        OperatingSystem.objects.create(name='foo', version='2.1')
        OperatingSystem.objects.create(name='bar', version='2.1')
        SystemStatus.objects.create(
            status='production', color='burgandy', color_code='wtf?'
        )
        Allocation.objects.create(name='something')
        self.client = Client()

    def client_tst(self, test_csv, save=True, primary_attr='hostname'):
        resp = self.client.post('/en-US/csv/ajax_csv_importer/', {
            'csv-data': test_csv, 'save': save, 'primary-attr': primary_attr
        })
        if resp.status_code != 200:
            # The exception thrown by csv_import is more useful than a status
            # code so we are running the function knowing it will fail. TODO,
            # figure out a better way for tests to know what went wrong.
            csv_import(test_csv, save=save)

    def test_get_related(self):
        test_csv = """
        hostname,operating_system%name
        baz.mozilla.com,foo
        """
        self.assertRaises(Exception, self.client_tst, test_csv)

        test_csv = """
        hostname,operating_system%name
        baz.mozilla.com,foo%foo
        """
        self.assertRaises(Exception, self.client_tst, test_csv)

        test_csv = """
        hostname,operating_system
        baz.mozilla.com,foo%foo
        """
        self.assertRaises(Exception, self.client_tst, test_csv)

        test_csv = """
        hostname,operating_system%version
        baz.mozilla.com,foo%foo
        """
        self.assertRaises(Exception, self.client_tst, test_csv)

        test_csv = """
        hostname,operating_system%name%version
        foobob.mozilla.com,foo%1.1
        """
        ret = csv_import(test_csv)
        self.assertEqual(1, len(ret))
        self.assertTrue(ret[0]['system'])

    def test_get_related_spaces(self):
        test_csv = """
        hostname, operating_system        %name
        baz.mozilla.com,foo
        """
        self.assertRaises(Exception, self.client_tst, test_csv)

        test_csv = """
        hostname, operating_system % name
        baz.mozilla.com,foo%foo
        """
        self.assertRaises(Exception, self.client_tst, test_csv)

        test_csv = """
        hostname,operating_system
        baz.mozilla.com, foo % foo
        """
        self.assertRaises(Exception, self.client_tst, test_csv)

        test_csv = """
        hostname,operating_system%version
        baz.mozilla.com,    foo %foo
        """
        self.assertRaises(Exception, self.client_tst, test_csv)

        test_csv = """
        hostname,operating_system%name%version
        foobob.mozilla.com,foo%  1.1
        """
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
        """
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
        """
        before = System.objects.all().count()
        ret = csv_import(test_csv, save=False)
        after = System.objects.all().count()
        self.assertEqual(9, len(ret))
        self.assertEqual(before, after)

    def test_keyvalue(self):
        test_csv = """
        hostname,nic.0.mac_address.0
        foobob.mozilla.com,keyvalue
        """
        ret = csv_import(test_csv, save=False)
        self.assertTrue(ret[0]['kvs'])

    def test_warranty_start_end(self):
        test_csv = """
        hostname,warranty_start,warranty_end
        foobob.mozilla.com,2011-03-01,2012-03-12
        """
        self.client_tst(test_csv, save=True)
        s = System.objects.get(hostname='foobob.mozilla.com')
        self.assertTrue(s.warranty_start)
        self.assertTrue(s.warranty_end)

    def test_invalid_field(self):
        test_csv = """
        hostname,warranty_start,warranty_end
        foobob.mozilla.com,2011-03-01,20192-03-12
        """
        self.assertRaises(ValueError, csv_import, test_csv, {'save': True})
        #s = System.objects.get(hostname='foobob.mozilla.com')
        #self.assertTrue(s.warranty_start)
        #self.assertTrue(s.warranty_end)

    def test_override(self):
        test_csv = """
        hostname,warranty_start,warranty_end
        foobob.mozilla.com,2011-03-01,2012-03-12
        """
        s = System.objects.create(hostname='foobob.mozilla.com', serial='1234')
        self.client_tst(test_csv, save=True)
        s = System.objects.get(hostname='foobob.mozilla.com')
        self.assertTrue(s.serial, '1234')

    def test_override_spaces(self):
        test_csv = """
        hostname , warranty_start,  warranty_end
        foobob.mozilla.com,   2011-03-01 , 2012-03-12
        """
        s = System.objects.create(hostname='foobob.mozilla.com', serial='1234')
        self.client_tst(test_csv, save=True)
        s = System.objects.get(hostname='foobob.mozilla.com')
        self.assertTrue(s.serial, '1234')

    def test_multiple_save(self):
        test_csv = """
        hostname
        foobob.mozilla.com
        foobob.mozilla.com
        """
        self.client_tst(test_csv, save=True)
        self.client_tst(test_csv, save=False)
        self.client_tst(test_csv, save=True)
        self.assertEqual(
            1, System.objects.filter(hostname='foobob.mozilla.com').count()
        )

    def test_invalid_mac(self):
        test_csv = """
        hostname,nic.0.mac_address.0
        foobob.mozilla.com,11:22:33:44:55:66:77
        """
        self.assertRaises(
            ValidationError, self.client_tst, test_csv, {'save': True}
        )

    def test_update_key_value(self):
        test_csv = """
        hostname,nic.0.name.0
        foobob.mozilla.com,nic0
        """
        self.client_tst(test_csv, save=True)
        s = System.objects.get(hostname='foobob.mozilla.com')
        self.assertEqual(1, s.keyvalue_set.filter(key='nic.0.name.0').count())
        self.assertEqual('nic0', s.keyvalue_set.get(key='nic.0.name.0').value)

        test_csv = """
        hostname,nic.0.name.0
        foobob.mozilla.com,nic33
        """
        self.client_tst(test_csv, save=True)
        s = System.objects.get(hostname='foobob.mozilla.com')
        self.assertEqual(1, s.keyvalue_set.filter(key='nic.0.name.0').count())
        self.assertEqual('nic33', s.keyvalue_set.get(key='nic.0.name.0').value)

        test_csv = """
        hostname,nic.0.mac_address.0
        foobob.mozilla.com,11:22:33:44:55:66
        """
        self.client_tst(test_csv, save=True)
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
        """
        self.client_tst(test_csv, save=False)
        self.client_tst(test_csv, save=True)
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
        """
        s = System.objects.create(hostname='foobob.mozilla.com')
        self.client_tst(test_csv, save=True)
        s = System.objects.get(hostname='foobob.mozilla.com')
        self.assertTrue(s.asset_tag, '1234')

        test_csv = """
        hostname,warranty_start,warranty_end,asset_tag
        changed-the-hostname.mozilla.com,2011-03-01,2012-03-12,1234
        """
        self.client_tst(test_csv, save=True, primary_attr='asset_tag')
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
        """
        self.assertRaises(
            ValidationError, self.client_tst, test_csv, {'save': True}
        )

    def test_primary_attribute(self):
        s = System.objects.create(hostname='foobob.mozilla.com')
        test_csv = """
        primary_attribute%hostname,hostname
        foobob.mozilla.com,foobar.mozilla.com
        """
        self.client_tst(test_csv, save=True, primary_attr='asset_tag')
        # The primary_attr kwarg shouldn't affect anything

        s1 = System.objects.get(pk=s.pk)
        self.assertEqual('foobar.mozilla.com', s1.hostname)

    def test_primary_attribute2(self):
        System.objects.create(
            hostname='foobob.mozilla.com', asset_tag='YM0090PW9G6'
        )
        test_csv = """
        primary_attribute%asset_tag,warranty_start,warranty_end,purchase_date
        YM0090PW9G6,2010-03-24,2013-03-24,2010-03-24
        """
        self.client_tst(test_csv, save=True)
        # The primary_attr kwarg shouldn't affect anything
        s1 = System.objects.get(asset_tag='YM0090PW9G6')
        self.assertTrue(s1.warranty_start)
        self.assertTrue(s1.warranty_end)

    def test_primary_attribute3(self):
        System.objects.create(
            hostname='foobob.mozilla.com', serial='SC07HT03WDKDJ'
        )
        test_csv = """
        primary_attribute%serial,warranty_start,warranty_end,purchase_date
        SC07HT03WDKDJ,2012-06-06,2013-06-06,2012-06-06
        """
        self.client_tst(test_csv, save=True)
        # The primary_attr kwarg shouldn't affect anything
        s1 = System.objects.get(serial='SC07HT03WDKDJ')
        self.assertEqual(
            datetime.datetime(2012, 6, 6, 0, 0).date(), s1.warranty_start)
        self.assertEqual(
            datetime.datetime(2013, 6, 6, 0, 0).date(), s1.warranty_end)

    def test_two_switches(self):
        System.objects.create(
            hostname='foobob.mozilla.com', serial='xxx'
        )
        test_csv = """
        primary_attribute%serial,switch_ports,ram
        xxx,"switch1.r101-10:xe-0/0/36,switch1.r101-10:xe-1/0/36",1000
        """
        self.client_tst(test_csv, save=True)
        # The primary_attr kwarg shouldn't affect anything
        s1 = System.objects.get(serial='xxx')
        self.assertEqual(
            s1.switch_ports,
            "switch1.r101-10:xe-0/0/36,switch1.r101-10:xe-1/0/36"
        )

    def test_quoted(self):
        System.objects.create(
            hostname='foobob.mozilla.com', serial='xxx'
        )
        test_csv = """
        hostname, switch_ports
        foobob.mozilla.com, "sdf,asfd,asfd"
        """
        self.client_tst(test_csv, save=True)
        # The primary_attr kwarg shouldn't affect anything
        s1 = System.objects.get(hostname='foobob.mozilla.com')
        self.assertEqual(s1.switch_ports, 'sdf,asfd,asfd')

    def test_allocation(self):
        l1 = Location.objects.create(
            name='loc1'
        )
        l2 = Location.objects.create(
            name='loc2'
        )
        SystemRack.objects.create(
            name='rack1', location=l1
        )
        SystemRack.objects.create(
            name='rack1', location=l2
        )
        test_csv = """hostname,system_status %status,system_rack %name,\
                        operating_system % name % version,allocation

        foobob.use1.mozilla.com,production, rack1 ,foo % 1.1,somthing
        """
        self.assertRaises(
            Exception, self.client_tst, test_csv)  # rack1 needs a location too
        self.assertFalse(
            System.objects.filter(hostname='foobob.use1.mozilla.com'))

        test_csv = """
        hostname,system_status %status,system_rack %name % location__name,\
                operating_system % name % version,allocation %name
foobob.use1.mozilla.com,production, rack1 % loc1,foo % 1.1,something
        """
        self.client_tst(test_csv, save=True)
