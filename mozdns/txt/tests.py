"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.core.exceptions import ValidationError

from mozdns.txt.models import TXT
from mozdns.domain.models import Domain


class TXTTests(TestCase):
    def setUp(self):
        self.o = Domain( name = "org" )
        self.o.save()
        self.o_e = Domain( name = "oregonstate.org")
        self.o_e.save()

    def do_generic_add(self, data ):
        txt = TXT( **data )
        txt.__repr__()
        txt.save()
        self.assertTrue(txt.details())
        self.assertTrue(txt.get_absolute_url())
        self.assertTrue(txt.get_edit_url())
        self.assertTrue(txt.get_delete_url())
        rtxt = TXT.objects.filter( **data )
        self.assertTrue( len(rtxt) == 1 )
        return txt

    def do_remove(self, data):
        txt = self.do_generic_add( data )
        txt.delete()
        rmx = TXT.objects.filter( **data )
        self.assertTrue( len(rmx) == 0 )

    def test_add_remove_txt(self):
        label = "asdf"
        data = "asdf"
        data = { 'label':label, 'txt_data':data ,'domain':self.o_e }
        txt1 = self.do_generic_add( data )

        label = "asdf"
        data = "asdfasfd"
        data = { 'label':label, 'txt_data':data ,'domain':self.o_e }
        txt1 = self.do_generic_add( data )

        label = "df"
        data = "aasdf"
        data = { 'label':label, 'txt_data':data ,'domain':self.o_e }
        txt1 = self.do_generic_add( data )

        label = "12314"
        data = "dd"
        data = { 'label':label, 'txt_data':data ,'domain':self.o }
        txt1 = self.do_generic_add( data )

