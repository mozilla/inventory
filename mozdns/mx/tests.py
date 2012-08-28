"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.core.exceptions import ValidationError

from mozdns.mx.models import MX
from mozdns.cname.models import CNAME
from mozdns.domain.models import Domain

import pdb

class MXTests(TestCase):

    def setUp(self):
        self.o = Domain( name = "org" )
        self.o.save()
        self.o_e = Domain( name = "oregonstate.org")
        self.o_e.save()
        self.b_o_e = Domain( name = "bar.oregonstate.org")
        self.b_o_e.save()

    def do_generic_add(self, data ):
        mx = MX( **data )
        mx.__repr__()
        mx.save()
        self.assertTrue(mx.details())
        self.assertTrue(mx.get_absolute_url())
        self.assertTrue(mx.get_edit_url())
        self.assertTrue(mx.get_delete_url())
        rmx = MX.objects.filter( **data )
        self.assertTrue( len(rmx) == 1 )
        return mx

    def test_add_mx(self):
        data = { 'label':'' ,'domain':self.o_e ,'server':'relay.oregonstate.edu' ,'priority':2 ,'ttl':2222 }
        self.do_generic_add( data )
        data = { 'label':'' ,'domain':self.o_e ,'server':'mail.sdf.fo' ,'priority':9 ,'ttl':34234 }
        self.do_generic_add( data )
        data = { 'label':'mail' ,'domain':self.b_o_e ,'server':'asdf.asdf' ,'priority':123 ,'ttl':213 }
        self.do_generic_add( data )
        data = { 'label':'' ,'domain':self.b_o_e ,'server':'oregonstate.edu' ,'priority':2 ,'ttl':2 }
        self.do_generic_add( data )
        data = { 'label':u'dsfasdfasdfasdfasdfasdfasdf' ,'domain':self.o ,'server':'nope.mail' ,'priority':12 ,'ttl':124 }
        self.do_generic_add( data )

    def test_add_invalid(self):
        data = { 'label': 'bar','domain':self.o_e,'server':'mail.oregonstate.edu','priority':123,'ttl':23}
        self.assertRaises(ValidationError, self.do_generic_add, data ) # TLD condition
        data = { 'label':'adsf,com' ,'domain':self.o_e ,'server':'mail.oregonstate.edu' ,'priority':123 ,'ttl':23 }
        self.assertRaises(ValidationError, self.do_generic_add, data )
        data = { 'label':'foo' ,'domain':self.o_e ,'server':'mail..com' ,'priority':34 ,'ttl':1234 }
        self.assertRaises(ValidationError, self.do_generic_add, data )
        data = { 'label':'foo.bar' ,'domain':self.o_e ,'server':'mail.com' ,'priority':3 ,'ttl':23424 }
        self.assertRaises(ValidationError, self.do_generic_add, data )
        data = { 'label':"asdf#$@" ,'domain':self.o_e ,'server':'coo.com' ,'priority':123 ,'ttl':23 }
        self.assertRaises(ValidationError, self.do_generic_add, data )
        data = { 'label':"asdf" ,'domain':self.o_e ,'server':'coo.com' ,'priority':-1 ,'ttl':23 }
        self.assertRaises(ValidationError, self.do_generic_add, data )
        data = { 'label':"asdf" ,'domain':self.o_e ,'server':'coo.com' ,'priority':65536 ,'ttl':23 }
        self.assertRaises(ValidationError, self.do_generic_add, data )
        data = { 'label':"asdf" ,'domain':self.o_e ,'server':234 ,'priority':65536 ,'ttl':23 }
        self.assertRaises(ValidationError, self.do_generic_add, data )

        data = { 'label':"a" ,'domain':self.o_e ,'server':'foo' ,'priority':6556 ,'ttl':91234241254 }
        self.assertRaises(ValidationError, self.do_generic_add, data )

    def do_remove(self, data):
        mx = self.do_generic_add( data )
        mx.delete()
        rmx = MX.objects.filter( **data )
        self.assertTrue( len(rmx) == 0 )

    def test_remove(self):
        data = { 'label':'' ,'domain':self.o_e ,'server':'frelay.oregonstate.edu' ,'priority':2 ,'ttl':2222 }
        self.do_remove( data )
        data = { 'label':'' ,'domain':self.o_e ,'server':'fmail.sdf.fo' ,'priority':9 ,'ttl':34234 }
        self.do_remove( data )
        data = { 'label':'mail' ,'domain':self.b_o_e ,'server':'asdff.asdf' ,'priority':123 ,'ttl':213 }
        self.do_remove( data )
        data = { 'label':'' ,'domain':self.b_o_e ,'server':'oregonsftate.edu' ,'priority':2 ,'ttl':2 }
        self.do_remove( data )
        data = { 'label':u'dsfasdfasdfasdfasdfasdfasdf' ,'domain':self.o ,'server':'nopef.mail' ,'priority':12 ,'ttl':124 }
        self.do_remove( data )

    def test_add_and_update_dup(self):
        data = { 'label':'' ,'domain':self.o_e ,'server':'relaydf.oregonstate.edu' ,'priority':2 ,'ttl':2222 }
        mx0 = self.do_generic_add( data )
        self.assertRaises( ValidationError, self.do_generic_add, data )
        data = { 'label':'' ,'domain':self.o_e ,'server':'mail.sddf.fo' ,'priority':9 ,'ttl':34234 }
        mx1 = self.do_generic_add( data )
        self.assertRaises( ValidationError, self.do_generic_add, data )

        mx0.server = "mail.sddf.fo"
        mx0.priority = 9
        mx0.ttl = 34234
        self.assertRaises( ValidationError, mx0.save )

    def test_add_with_cname(self):
        label = "cnamederp"
        domain = self.o_e
        data = "foo.com"
        cn = CNAME( label = label, domain = domain, target = data )
        cn.full_clean()
        cn.save()

        data = { 'label':'' ,'domain':self.o_e ,'server':'cnamederp.oregonstate.org' ,'priority':2 ,'ttl':2222 }
        mx = MX( **data )
        self.assertRaises( ValidationError, mx.save )

