from django.core.exceptions import ValidationError
from django.test import TestCase
from django.test.client import Client

from mozdns.domain.models import Domain
from mozdns.address_record.models import AddressRecord
from mozdns.nameserver.models import Nameserver

from mozdns.ip.models import ipv6_to_longs, Ip
from mozdns.ip.utils import ip2dns_form


class NSTestsModels(TestCase):
    def create_domain(self, name, ip_type=None, delegated=False):
        if ip_type is None:
            ip_type = '4'
        if name in ('arpa', 'in-addr.arpa', 'ipv6.arpa'):
            pass
        else:
            name = ip2dns_form(name, ip_type=ip_type)
        d = Domain(name = name, delegated=delegated)
        d.clean()
        self.assertTrue(d.is_reverse)
        return d

    def setUp(self):
        self.arpa = self.create_domain( name = 'arpa')
        self.arpa.save()
        self.i_arpa = self.create_domain( name = 'in-addr.arpa')
        self.i_arpa.save()
        self.i6_arpa = self.create_domain( name = 'ipv6.arpa')
        self.i6_arpa.save()

        self.r = Domain( name = "ru" )
        self.r.save()
        self.f_r = Domain( name = "foo.ru" )
        self.f_r.save()
        self.b_f_r = Domain( name = "bar.foo.ru" )
        self.b_f_r.save()

        self.f = Domain( name = "fam" )
        self.f.save()

        self._128 = self.create_domain( name = '128', ip_type= '4' )
        self._128.save()

    def do_add(self, domain, server):
        ns = Nameserver( domain = domain, server = server)
        ns.save()
        ns.save()
        self.assertTrue(ns.__repr__())
        self.assertTrue(ns.details())
        self.assertTrue(ns.get_absolute_url())
        self.assertTrue(ns.get_edit_url())
        self.assertTrue(ns.get_delete_url())
        ret = Nameserver.objects.filter( domain = domain, server = server )
        self.assertEqual( len(ret), 1 )
        return ns

    def test_add_TLD(self):
        data = { 'domain':self.r , 'server':'bar.foo.ru' }
        self.assertRaises( ValidationError, self.do_add, **data )

    def test_add_ns(self):
        data = { 'domain':self.r , 'server':'ns2.moot.ru' }
        self.do_add( **data )

        data = { 'domain':self.r , 'server':'ns5.moot.ru' }
        self.do_add( **data )

        data = { 'domain':self.r , 'server':u'ns3.moot.ru' }
        self.do_add( **data )

        data = { 'domain':self.b_f_r , 'server':'n1.moot.ru' }
        self.do_add( **data )

        data = { 'domain':self.b_f_r , 'server':'ns2.moot.ru' }
        self.do_add( **data )

        data = { 'domain':self.r , 'server':'asdf.asdf' }
        self.do_add( **data )

    def test_add_invalid(self):
        data = { 'domain':self.f_r , 'server':'ns3.foo.ru' }
        self.assertRaises( ValidationError, self.do_add, **data  )

    def testtest_add_ns_in_domain(self):
        glue = AddressRecord( label='ns2', domain = self.r, ip_str = '128.193.1.10', ip_type='4' )
        glue.save()
        data = { 'domain':self.r , 'server':'ns2.ru' }
        ns = self.do_add( **data )
        self.assertTrue( ns.glue )
        self.assertEqual( ns.server, ns.glue.fqdn )

        glue = AddressRecord( label='ns3', domain = self.f_r, ip_str = '128.193.1.10', ip_type='4' )
        glue.save()
        data = { 'domain':self.f_r , 'server':'ns3.foo.ru' }
        ns = self.do_add( **data )
        self.assertTrue( ns.glue )
        self.assertEqual( ns.server, ns.glue.fqdn )

    def test_add_ns_outside_domain(self):
        data = { 'domain':self.f_r , 'server':'ns2.ru' }
        ns = self.do_add( **data )
        self.assertFalse( ns.glue )

    def test_update_glue_to_no_glue(self):
        glue = AddressRecord( label='ns3', domain = self.r, ip_str = '128.193.1.10', ip_type='4' )
        glue.save()
        data = { 'domain':self.r , 'server':'ns3.ru' }
        ns = self.do_add( **data )
        self.assertTrue( ns.glue )

        ns.server = "ns4.wee"
        ns.save()
        self.assertTrue( ns.glue == None )



    def test_delete_ns(self):
        glue = AddressRecord( label='ns4', domain = self.f_r, ip_str = '128.196.1.10', ip_type='4' )
        glue.save()
        data = { 'domain':self.f_r , 'server':'ns4.foo.ru' }
        ns = self.do_add( **data )
        self.assertTrue( ns.glue )
        self.assertEqual( ns.server, ns.glue.fqdn )

        ns.delete()
        nsret = Nameserver.objects.filter( server = 'ns2.foo.ru', domain = self.f_r )
        self.assertFalse( nsret )

    def test_invalid_create(self):
        glue = AddressRecord( label='ns2', domain = self.r, ip_str = '128.193.1.10', ip_type = '4' )
        glue.save()

        data = { 'domain':self.r , 'server':'ns2 .ru' }
        self.assertRaises( ValidationError, self.do_add, **data )
        data = { 'domain':self.r , 'server':'ns2$.ru' }
        self.assertRaises( ValidationError, self.do_add, **data )
        data = { 'domain':self.r , 'server':'ns2..ru' }
        self.assertRaises( ValidationError, self.do_add, **data )
        data = { 'domain':self.r , 'server':'ns2.ru ' }
        self.assertRaises( ValidationError, self.do_add, **data )
        data = { 'domain':self.r , 'server':'' }
        self.assertRaises( ValidationError, self.do_add, **data )

    def test_add_dup(self):
        data = { 'domain':self.r , 'server':'ns2.moot.ru' }
        self.do_add( **data )

        self.assertRaises( ValidationError, self.do_add, **data)
