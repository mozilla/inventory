from django.core.exceptions import ValidationError
from django.test import TestCase, RequestFactory

from mozdns.domain.models import Domain
from mozdns.address_record.models import AddressRecord
from mozdns.nameserver.models import Nameserver
from mozdns.ptr.models import PTR
from mozdns.cname.models import CNAME
from mozdns.soa.models import SOA
from mozdns.ip.utils import ip_to_domain_name

from core.interface.static_intr.models import StaticInterface
from systems.models import System

from mozdns.tests.utils import create_fake_zone


class NSTestsModels(TestCase):
    def create_domain(self, name, ip_type=None, delegated=False):
        if ip_type is None:
            ip_type = '4'
        if name in ('arpa', 'in-addr.arpa', 'ip6.arpa'):
            pass
        else:
            name = ip_to_domain_name(name, ip_type=ip_type)
        d = Domain(name = name, delegated=delegated)
        d.clean()
        self.assertTrue(d.is_reverse)
        return d

    def setUp(self):
        self.factory = RequestFactory()
        self.arpa = self.create_domain(name = 'arpa')
        self.arpa.save()
        self.i_arpa = self.create_domain(name = 'in-addr.arpa')
        self.i_arpa.save()
        self.i6_arpa = self.create_domain(name = 'ip6.arpa')
        self.i6_arpa.save()

        self.r = Domain(name = "ru")
        self.r.save()
        self.f_r = Domain(name = "foo.ru")
        self.f_r.save()
        self.b_f_r = Domain(name = "bar.foo.ru")
        self.b_f_r.save()

        self.f = Domain(name = "fam")
        self.f.save()

        self._128 = self.create_domain(name = '128', ip_type= '4')
        self._128.save()

        self.s = System()
        self.s.save()

    def do_add(self, domain, server):
        ns = Nameserver(domain = domain, server = server)
        ns.save()
        self.assertTrue(ns.__repr__())
        self.assertTrue(ns.details())
        self.assertTrue(ns.get_absolute_url())
        self.assertTrue(ns.get_edit_url())
        self.assertTrue(ns.get_delete_url())
        ret = Nameserver.objects.filter(domain = domain, server = server)
        self.assertEqual(len(ret), 1)
        return ns

    def test_add_ns(self):
        data = {'domain':self.r , 'server':'ns2.moot.ru'}
        self.do_add(**data)

        data = {'domain':self.r , 'server':'ns5.moot.ru'}
        self.do_add(**data)

        data = {'domain':self.r , 'server':u'ns3.moot.ru'}
        self.do_add(**data)

        data = {'domain':self.b_f_r , 'server':'n1.moot.ru'}
        self.do_add(**data)

        data = {'domain':self.b_f_r , 'server':'ns2.moot.ru'}
        self.do_add(**data)

        data = {'domain':self.r , 'server':'asdf.asdf'}
        self.do_add(**data)

    def test_add_invalid(self):
        data = {'domain':self.f_r , 'server':'ns3.foo.ru'}
        self.assertRaises(ValidationError, self.do_add, **data )

        data = {'domain':self.f_r , 'server':''}
        self.assertRaises(ValidationError, self.do_add, **data )

    def testtest_add_ns_in_domain(self):
        # Use an A record as a glue record.
        glue = AddressRecord(label='ns2', domain = self.r, ip_str = '128.193.1.10', ip_type='4')
        glue.clean()
        glue.save()
        data = {'domain':self.r , 'server':'ns2.ru'}
        ns = self.do_add(**data)
        self.assertTrue(ns.glue)
        self.assertEqual(ns.server, ns.glue.fqdn)
        self.assertRaises(ValidationError, glue.delete)

        glue = AddressRecord(label='ns3', domain = self.f_r, ip_str =
                             '128.193.1.10', ip_type='4')
        glue.save()
        data = {'domain':self.f_r , 'server':'ns3.foo.ru'}
        ns = self.do_add(**data)
        self.assertTrue(ns.glue)
        self.assertEqual(ns.server, ns.glue.fqdn)

    def test_disallow_name_update_of_glue_A(self):
        # Glue records should not be allowed to change their name.
        glue = AddressRecord(label='ns39', domain = self.f_r, ip_str =
                             '128.193.1.77', ip_type='4')
        glue.clean()
        glue.save()
        data = {'domain':self.f_r , 'server':'ns39.foo.ru'}
        ns = self.do_add(**data)
        self.assertTrue(ns.glue)
        self.assertEqual(ns.glue, glue)

        glue.label = "ns22"
        self.assertRaises(ValidationError, glue.clean)

    def test_disallow_name_update_of_glue_Intr(self):
        # Glue records should not be allowed to change their name.
        glue = StaticInterface(label='ns24', domain = self.f_r, ip_str =
                '128.193.99.10', ip_type='4', system=self.s,
                mac="11:22:33:44:55:66")
        glue.clean()
        glue.save()
        data = {'domain':self.f_r , 'server':'ns24.foo.ru'}
        ns = self.do_add(**data)
        self.assertTrue(ns.glue)
        self.assertEqual(ns.glue, glue)

        glue.label = "ns22"
        self.assertRaises(ValidationError, glue.clean)

    def test_disallow_delete_of_glue_intr(self):
        # Interface glue records should not be allowed to be deleted.
        glue = StaticInterface(label='ns24', domain = self.f_r, ip_str =
                '128.193.99.10', ip_type='4', system=self.s,
                mac="11:22:33:44:55:66")
        glue.clean()
        glue.save()
        data = {'domain':self.f_r , 'server':'ns24.foo.ru'}
        ns = self.do_add(**data)
        self.assertTrue(ns.glue)
        self.assertEqual(ns.glue, glue)

        self.assertRaises(ValidationError, glue.delete)

    def test_manual_assign_of_glue(self):
        # Test that assigning a different glue record doesn't get overriden by
        # the auto assinging during the Nameserver's clean function.
        glue = StaticInterface(label='ns25', domain = self.f_r, ip_str =
                '128.193.99.10', ip_type='4', system=self.s,
                mac="11:22:33:44:55:66")
        glue.clean()
        glue.save()
        data = {'domain':self.f_r, 'server':'ns25.foo.ru'}
        ns = self.do_add(**data)
        self.assertTrue(ns.glue)
        self.assertEqual(ns.glue, glue)

        glue2 = AddressRecord(label='ns25', domain = self.f_r, ip_str =
                '128.193.1.78', ip_type='4')
        glue2.clean()
        glue2.save()

        ns.clean()

        # Make sure things didn't get overriden.
        self.assertEqual(ns.glue, glue)

        ns.glue = glue2
        ns.save()
        # Refresh the object
        ns = Nameserver.objects.get(pk=ns.pk)
        # Again, Make sure things didn't get overriden.
        self.assertEqual(ns.glue, glue2)
        # Make sure we still can't delete.
        self.assertRaises(ValidationError, glue2.delete)
        self.assertRaises(ValidationError, ns.glue.delete)

        # We shuold be able to delelte the other one.
        glue.delete()


    def testtest_add_ns_in_domain_intr(self):
        # Use an Interface as a glue record.
        glue = StaticInterface(label='ns232', domain = self.r, ip_str =
                '128.193.99.10', ip_type='4', system=self.s,
                mac="12:23:45:45:45:45")
        glue.clean()
        glue.save()
        data = {'domain':self.r , 'server':'ns232.ru'}
        ns = self.do_add(**data)
        self.assertTrue(ns.glue)
        self.assertEqual(ns.server, ns.glue.fqdn)
        self.assertRaises(ValidationError, glue.delete)

        glue = StaticInterface(label='ns332', domain = self.f_r, ip_str =
                '128.193.1.10', ip_type='4', system=self.s,
                mac="11:22:33:44:55:66")
        glue.clean()
        glue.save()
        data = {'domain':self.f_r , 'server':'ns332.foo.ru'}
        ns = self.do_add(**data)
        self.assertTrue(ns.glue)
        self.assertEqual(ns.server, ns.glue.fqdn)

    def test_add_ns_outside_domain(self):
        data = {'domain':self.f_r , 'server':'ns2.ru'}
        ns = self.do_add(**data)
        self.assertFalse(ns.glue)

    def test_update_glue_to_no_intr(self):
        glue = StaticInterface(label='ns34', domain = self.r, ip_str =
                '128.193.1.10', ip_type='4', system=self.s,
                mac="11:22:33:44:55:66")
        glue.save()
        data = {'domain':self.r , 'server':'ns34.ru'}
        ns = self.do_add(**data)
        self.assertTrue(ns.glue)

        ns.server = "ns4.wee"
        ns.save()
        self.assertTrue(ns.glue == None)

    def test_update_glue_record_intr(self):
        # Glue records can't change their name.
        glue = StaticInterface(label='ns788', domain = self.r, ip_str =
                '128.193.1.10', ip_type='4', system=self.s,
                mac="11:22:33:44:55:66")
        glue.save()
        data = {'domain':self.r , 'server':'ns788.ru'}
        ns = self.do_add(**data)
        self.assertTrue(ns.glue)
        glue.label = "asdfasdf"
        self.assertRaises(ValidationError, glue.clean)

    def test_update_glue_to_no_glue(self):
        glue = AddressRecord(label='ns3', domain = self.r, ip_str = '128.193.1.10', ip_type='4')
        glue.save()
        data = {'domain':self.r , 'server':'ns3.ru'}
        ns = self.do_add(**data)
        self.assertTrue(ns.glue)

        ns.server = "ns4.wee"
        ns.save()
        self.assertTrue(ns.glue == None)



    def test_delete_ns(self):
        glue = AddressRecord(label='ns4', domain = self.f_r, ip_str = '128.196.1.10', ip_type='4')
        glue.save()
        data = {'domain':self.f_r , 'server':'ns4.foo.ru'}
        ns = self.do_add(**data)
        self.assertTrue(ns.glue)
        self.assertEqual(ns.server, ns.glue.fqdn)

        ns.delete()
        nsret = Nameserver.objects.filter(server = 'ns2.foo.ru', domain = self.f_r)
        self.assertFalse(nsret)

    def test_invalid_create(self):
        glue = AddressRecord(label='ns2', domain = self.r, ip_str = '128.193.1.10', ip_type = '4')
        glue.save()

        data = {'domain':self.r , 'server':'ns2 .ru'}
        self.assertRaises(ValidationError, self.do_add, **data)
        data = {'domain':self.r , 'server':'ns2$.ru'}
        self.assertRaises(ValidationError, self.do_add, **data)
        data = {'domain':self.r , 'server':'ns2..ru'}
        self.assertRaises(ValidationError, self.do_add, **data)
        data = {'domain':self.r , 'server':'ns2.ru '}
        self.assertRaises(ValidationError, self.do_add, **data)
        data = {'domain':self.r , 'server':''}
        self.assertRaises(ValidationError, self.do_add, **data)

    def test_add_dup(self):
        data = {'domain':self.r , 'server':'ns2.moot.ru'}
        self.do_add(**data)

        self.assertRaises(ValidationError, self.do_add, **data)

    def _get_post_data(self, random_str):
        """Return a valid set of data"""
        return {
            'root_domain': '{0}.mozilla.com'.format(random_str),
            'soa_primary': 'ns1.mozilla.com',
            'soa_contact': 'noc.mozilla.com',
            'nameserver_1': 'ns1.mozilla.com',
            'ttl_1': '1234'
        }

    def test_bad_nameserver_soa_state_case_1_0(self):
        # This is Case 1
        root_domain = create_fake_zone("asdf10")
        for ns in root_domain.nameserver_set.all():
            ns.delete()

        # At his point we should have a domain at the root of a zone with no
        # other records in it.

        # Adding a record shouldn't be allowed because there is no NS record on
        # the zone's root domain.
        a = AddressRecord(label='', domain=root_domain, ip_type="6", ip_str="1::")
        self.assertRaises(ValidationError, a.save)
        cn = CNAME(label='', domain=root_domain, target="asdf")
        self.assertRaises(ValidationError, cn.save)

    def test_bad_nameserver_soa_state_case_1_1(self):
        # This is Case 1
        root_domain = create_fake_zone("asdf111")
        for ns in root_domain.nameserver_set.all():
            ns.delete()

        # At his point we should have a domain at the root of a zone with no
        # other records in it.

        # Let's create a child domain and try to add a record there.
        cdomain = Domain(name="test." + root_domain.name)
        cdomain.soa = root_domain.soa
        cdomain.save()

        # Adding a record shouldn't be allowed because there is no NS record on
        # the zone's root domain.
        a = AddressRecord(label='', domain=cdomain, ip_type="6", ip_str="1::")
        self.assertRaises(ValidationError, a.save)
        cn = CNAME(label='', domain=cdomain, target="asdf")
        self.assertRaises(ValidationError, cn.save)

    def test_bad_nameserver_soa_state_case_1_2(self):
        # This is Case 1 ... with ptr's
        root_domain = create_fake_zone("12.in-addr.arpa", suffix="")
        for ns in root_domain.nameserver_set.all():
            ns.delete()

        # At his point we should have a domain at the root of a zone with no
        # other records in it.

        # Adding a record shouldn't be allowed because there is no NS record on
        # the zone's root domain.
        ptr = PTR(name="asdf", ip_str="12.10.1.1", ip_type="4")
        self.assertRaises(ValidationError, ptr.save)

    def test_bad_nameserver_soa_state_case_1_3(self):
        # This is Case 1 ... with ptr's
        root_domain = create_fake_zone("13.in-addr.arpa", suffix="")
        for ns in root_domain.nameserver_set.all():
            ns.delete()

        # At his point we should have a domain at the root of a zone with no
        # other records in it.

        # Let's create a child domain and try to add a record there.
        cdomain = Domain(name="10.13.in-addr.arpa")
        cdomain.soa = root_domain.soa
        cdomain.save()

        # Adding a record shouldn't be allowed because there is no NS record on
        # the zone's root domain.
        ptr = PTR(name="asdf", ip_str="13.10.1.1", ip_type="4")
        self.assertRaises(ValidationError, ptr.save)

    def test_bad_nameserver_soa_state_case_2_0(self):
        # This is Case 2
        root_domain = create_fake_zone("asdf20")
        self.assertEqual(root_domain.nameserver_set.count(), 1)
        ns = root_domain.nameserver_set.all()[0]

        # At his point we should have a domain at the root of a zone with one
        # ns record associated to the domain.

        a = AddressRecord(label='', domain=root_domain, ip_type="6", ip_str="1::")
        a.save()

        self.assertRaises(ValidationError, ns.delete)

    def test_bad_nameserver_soa_state_case_2_1(self):
        # This is Case 2
        root_domain = create_fake_zone("asdf21")
        self.assertEqual(root_domain.nameserver_set.count(), 1)
        ns = root_domain.nameserver_set.all()[0]

        # At his point we should have a domain at the root of a zone with one
        # ns record associated to the domain.

        # Let's create a child domain and add a record there, then try to
        # delete the NS record
        cdomain = Domain(name="test." + root_domain.name)
        cdomain.soa = root_domain.soa
        cdomain.save()

        a = AddressRecord(label='', domain=cdomain, ip_type="6", ip_str="1::")
        a.save()

        self.assertRaises(ValidationError, ns.delete)

    def test_bad_nameserver_soa_state_case_2_2(self):
        # This is Case 2 ... with ptrs
        root_domain = create_fake_zone("22.in-addr.arpa", suffix="")
        self.assertEqual(root_domain.nameserver_set.count(), 1)
        ns = root_domain.nameserver_set.all()[0]

        # At his point we should have a domain at the root of a zone with one
        # ns record associated to the domain.

        ptr = PTR(name="asdf", ip_str="22.1.1.1", ip_type="4")
        ptr.save()

        self.assertRaises(ValidationError, ns.delete)

    def test_bad_nameserver_soa_state_case_2_3(self):
        # This is Case 2 ... with ptrs
        root_domain = create_fake_zone("10.23.in-addr.arpa", suffix="")
        self.assertEqual(root_domain.nameserver_set.count(), 1)
        ns = root_domain.nameserver_set.all()[0]

        # At his point we should have a domain at the root of a zone with one
        # ns record associated to the domain.

        # Let's create a child domain and add a record there, then try to
        # delete the NS record
        cdomain = Domain(name="test." + root_domain.name)
        cdomain.soa = root_domain.soa
        cdomain.save()

        ptr = PTR(name="asdf", ip_str="23.10.1.1", ip_type="4")
        ptr.save()

        self.assertRaises(ValidationError, ns.delete)

    def test_bad_nameserver_soa_state_case_3_0(self):
        # This is Case 3
        root_domain = create_fake_zone("asdf30")
        for ns in root_domain.nameserver_set.all():
            ns.delete()

        soa = ns.domain.soa
        ns.domain.soa = None
        root_domain.soa = None  # Shit's getting cached
        ns.domain.save()
        soa.delete()

        # At his point we should have a domain pointed at no SOA record with no
        # records attached to it. It also has no child domains.

        # Add a record to the domain.
        a = AddressRecord(label='', domain=root_domain, ip_type="6", ip_str="1::")
        a.save()

        s = SOA(primary="asdf.asdf", contact="asdf.asdf", description="asdf")
        s.save()
        root_domain.soa = s

        self.assertRaises(ValidationError, root_domain.save)

    def test_bad_nameserver_soa_state_case_3_1(self):
        # This is Case 3
        root_domain = create_fake_zone("asdf31")
        for ns in root_domain.nameserver_set.all():
            ns.delete()


        # At his point we should have a domain pointed at an SOA record with no
        # records attached to it (esspecially no ns recods). It also has no
        # child domains.

        # Try case 3 but add a record to a child domain of root_domain
        cdomain = Domain(name="test." + root_domain.name)
        cdomain.save()

        # Add a record to the domain.
        a = AddressRecord(label='', domain=cdomain, ip_type="6", ip_str="1::")
        a.save()

        # Now try to add the domain to the zone that has no NS records at it's
        # root
        cdomain.soa = root_domain.soa

        self.assertRaises(ValidationError, cdomain.save)

    def test_bad_nameserver_soa_state_case_3_2(self):
        # This is Case 3 ... with ptrs
        root_domain = create_fake_zone("32.in-addr.arpa", suffix="")
        for ns in root_domain.nameserver_set.all():
            ns.delete()

        soa = ns.domain.soa
        ns.domain.soa = None
        root_domain.soa = None  # Shit's getting cached
        ns.domain.save()
        soa.delete()

        # At his point we should have a domain pointed at no SOA record with no
        # records attached to it. It also has no child domains.

        # Add a record to the domain.

        ptr = PTR(name="asdf", ip_str="32.1.1.1", ip_type="4")
        ptr.save()

        s = SOA(primary="asdf.asdf", contact="asdf.asdf", description="asdf")
        s.save()
        root_domain.soa = s

        self.assertRaises(ValidationError, root_domain.save)

    def test_bad_nameserver_soa_state_case_3_3(self):
        # This is Case 3 ... with ptrs
        root_domain = create_fake_zone("33.in-addr.arpa", suffix="")
        for ns in root_domain.nameserver_set.all():
            ns.delete()


        # At his point we should have a domain pointed at an SOA record with no
        # records attached to it (esspecially no ns recods). It also has no
        # child domains.

        # Try case 3 but add a record to a child domain of root_domain
        cdomain = Domain(name="10.33.in-addr.arpa")
        cdomain.save()

        # Add a record to the domain.
        ptr = PTR(name="asdf", ip_str="33.10.1.1", ip_type="4")
        ptr.save()

        # Now try to add the domain to the zone that has no NS records at it's
        # root
        cdomain.soa = root_domain.soa

        self.assertRaises(ValidationError, cdomain.save)
