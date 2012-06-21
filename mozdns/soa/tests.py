"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.core.exceptions import ValidationError

from mozdns.soa.models import *
from mozdns.domain.models import Domain


class SOATests(TestCase):
    def setUp(self):
        pass

    def do_generic_add(self, primary, contact, retry, refresh, comment):
        soa = SOA( primary = primary, contact = contact, retry = retry, refresh = refresh, comment= comment )
        soa.save()
        soa.save()
        rsoa = SOA.objects.filter( primary = primary, contact = contact, retry = retry, refresh=refresh )
        self.assertTrue( len(rsoa) == 1 )
        return soa

    def test_add_soa(self):
        primary = "ns1.oregonstate.edu"
        contact = "admin.oregonstate.edu"
        retry = 1234
        refresh = 1234123
        comment = "1"
        self.do_generic_add(primary, contact,retry, refresh, comment=comment)
        soa = SOA.objects.filter( primary = primary, contact = contact, retry = retry, refresh = refresh )
        soa[0].save()
        self.assertTrue( soa )
        soa[0].__repr__()
        soa = soa[0]
        self.assertTrue(soa.details())
        self.assertTrue(soa.get_absolute_url())
        self.assertTrue(soa.get_edit_url())
        self.assertTrue(soa.get_delete_url())

        primary = "do.com"
        contact = "admf.asdf"
        retry = 432152
        refresh = 1235146134
        comment = "2"
        self.do_generic_add(primary, contact,retry, refresh, comment=comment)
        soa = SOA.objects.filter( primary = primary, contact = contact, retry = retry, refresh = refresh )
        self.assertTrue( soa )
        soa = soa[0]
        self.assertTrue(soa.details())
        self.assertTrue(soa.get_absolute_url())
        self.assertTrue(soa.get_edit_url())
        self.assertTrue(soa.get_delete_url())

        primary = "ns1.derp.com"
        contact = "admf.asdf"
        soa = SOA( primary = primary, contact = contact )
        soa.save()
        self.assertTrue( soa.serial and soa.expire and soa.retry and soa.refresh )
        self.assertTrue(soa.details())
        self.assertTrue(soa.get_absolute_url())
        self.assertTrue(soa.get_edit_url())
        self.assertTrue(soa.get_delete_url())

    def test_add_remove(self):
        primary = "ns2.oregonstate.edu"
        contact = "admin.oregonstate.edu"
        retry = 1234
        refresh = 1234123
        comment = "3"
        soa = self.do_generic_add(primary, contact,retry, refresh, comment=comment)
        soa.delete()
        soa = SOA.objects.filter( primary = primary, contact = contact, retry = retry, refresh=refresh )
        self.assertTrue( len(soa) == 0 )

        primary = "dddo.com"
        contact = "admf.asdf"
        retry = 432152
        refresh = 1235146134
        comment = "4"
        soa = self.do_generic_add(primary, contact,retry, refresh, comment=comment)
        soa.delete()
        soa = SOA.objects.filter( primary = primary, contact = contact, retry = retry, refresh=refresh, comment=comment )
        self.assertTrue( len(soa) == 0 )

        # Add dup
        comment = "4"
        soa = self.do_generic_add(primary, contact,retry, refresh, comment=comment)
        soa.save()
        self.assertRaises(ValidationError, self.do_generic_add, *(primary, contact,retry, refresh, comment))

    def test_add_invalid(self):
        data = { 'primary':"daf..fff" , 'contact':"foo.com" }
        soa = SOA(**data)
        self.assertRaises(ValidationError, soa.save)
        data = { 'primary':'foo.com' , 'contact':'dkfa..' }
        soa = SOA(**data)
        self.assertRaises(ValidationError, soa.save)
        data = { 'primary':'adf' , 'contact':'*@#$;' }
        soa = SOA(**data)
        self.assertRaises(ValidationError, soa.save)

    def test_chain_soa_domain_add(self):
        data = { 'primary':"ns1.foo.com" , 'contact':"email.foo.com" }
        soa = SOA(**data)
        soa.save()
        d0 = Domain( name = 'com' )
        d0.save()
        d1 = Domain( name = 'foo.com', soa = soa )
        d1.save()
        self.assertTrue( soa == d1.soa )
        d2 = Domain( name = 'bar.foo.com', soa = soa )
        d2.save()
        self.assertTrue( soa == d2.soa )
        d3 = Domain( name = 'new.foo.com', soa = soa )
        d3.save()
        self.assertTrue( soa == d3.soa )
        d4 = Domain( name = 'far.bar.foo.com', soa = soa )
        d4.save()
        self.assertTrue( soa == d4.soa )
        d5 = Domain( name = 'tee.new.foo.com', soa = soa )
        d5.save()
        self.assertTrue( soa == d5.soa )
        d5.delete()
        d4.delete()
        self.assertTrue( soa == d1.soa )
        self.assertTrue( soa == d2.soa )
        self.assertTrue( soa == d3.soa )
