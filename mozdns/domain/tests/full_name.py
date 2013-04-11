from django.test import TestCase

from mozdns.address_record.models import AddressRecord
from mozdns.cname.models import CNAME
from mozdns.txt.models import TXT
from mozdns.mx.models import MX
from mozdns.srv.models import SRV
from mozdns.domain.models import Domain
from mozdns.nameserver.models import Nameserver
from mozdns.utils import ensure_label_domain, prune_tree
from mozdns.soa.models import SOA

from mozdns.tests.utils import create_fake_zone


class FullNameTests(TestCase):

    def test_basic_add_remove1(self):
        c = Domain(name='com')
        c.save()
        self.assertFalse(c.purgeable)
        f_c = Domain(name='foo.com')
        s, _ = SOA.objects.get_or_create(primary="foo", contact="foo",
                                         description="foo.zfoo.comom")
        f_c.soa = s
        f_c.save()
        self.assertFalse(f_c.purgeable)
        fqdn = "bar.x.y.z.foo.com"
        label, the_domain = ensure_label_domain(fqdn)
        self.assertEqual(label, "bar")
        self.assertEqual(the_domain.name, "x.y.z.foo.com")
        self.assertTrue(the_domain.purgeable)
        self.assertEqual(the_domain.master_domain.name, "y.z.foo.com")
        self.assertTrue(the_domain.master_domain.purgeable)
        self.assertEqual(
            the_domain.master_domain.master_domain.name, "z.foo.com")
        self.assertTrue(the_domain.master_domain.master_domain.purgeable)
        self.assertEqual(
            the_domain.master_domain.master_domain.master_domain.name,
            "foo.com")
        self.assertFalse(
            the_domain.master_domain.master_domain.master_domain.purgeable)

        # Now call prune tree one the_domain
        self.assertTrue(prune_tree(the_domain))

        self.assertFalse(Domain.objects.filter(name="x.y.z.foo.com"))
        self.assertFalse(Domain.objects.filter(name="y.z.foo.com"))
        self.assertFalse(Domain.objects.filter(name="z.foo.com"))
        self.assertTrue(Domain.objects.filter(name="foo.com"))

        # Make sure other domain's can't be pruned
        self.assertFalse(prune_tree(f_c))
        self.assertTrue(Domain.objects.filter(name="foo.com"))
        self.assertFalse(prune_tree(c))
        self.assertTrue(Domain.objects.filter(name="com"))

    def test_basic_add_remove2(self):
        # MAke sure that if a domain is set to not purgeable the prune stops at
        # that domain.
        c = Domain(name='edu')
        c.save()
        self.assertFalse(c.purgeable)
        f_c = Domain(name='foo.edu')
        s, _ = SOA.objects.get_or_create(primary="foo", contact="foo",
                                         description="foo.edu")
        f_c.soa = s
        f_c.save()
        self.assertFalse(f_c.purgeable)
        fqdn = "bar.x.y.z.foo.edu"
        label, the_domain = ensure_label_domain(fqdn)
        self.assertEqual(label, "bar")
        self.assertEqual(the_domain.name, "x.y.z.foo.edu")
        self.assertTrue(the_domain.purgeable)
        self.assertEqual(the_domain.master_domain.name, "y.z.foo.edu")
        self.assertTrue(the_domain.master_domain.purgeable)
        self.assertEqual(
            the_domain.master_domain.master_domain.name, "z.foo.edu")
        self.assertTrue(the_domain.master_domain.master_domain.purgeable)
        self.assertEqual(
            the_domain.master_domain.master_domain.master_domain.name,
            "foo.edu")
        self.assertFalse(
            the_domain.master_domain.master_domain.master_domain.purgeable)

        # See if purgeable stops prune
        the_domain.purgeable = False
        the_domain.save()
        self.assertFalse(prune_tree(the_domain))
        the_domain.purgeable = True
        the_domain.save()
        # Ok, reset

        y_z = Domain.objects.get(name="y.z.foo.edu")
        y_z.purgeable = False
        y_z.save()

        # Refresh the domain
        the_domain = Domain.objects.get(pk=the_domain.pk)
        # This should delete up to and stop at the domain "y.z.foo.edu"
        self.assertTrue(prune_tree(the_domain))

        self.assertFalse(Domain.objects.filter(name="x.y.z.foo.edu"))
        self.assertTrue(Domain.objects.filter(name="y.z.foo.edu"))
        self.assertTrue(Domain.objects.filter(name="z.foo.edu"))
        self.assertTrue(Domain.objects.filter(name="foo.edu"))

        # If we delete y.z.foo.com and then call prune on z.foo.com is should
        # delete z.foo.com
        Domain.objects.get(name="y.z.foo.edu").delete()

        self.assertTrue(prune_tree(Domain.objects.get(name="z.foo.edu")))
        self.assertFalse(Domain.objects.filter(name="z.foo.edu"))
        self.assertTrue(Domain.objects.filter(name="foo.edu"))

    def test_basic_add_remove3(self):
        # MAke sure that if a domain is set to not purgeable the prune stops at
        # that domain when a record exists in a domain
        f_c = create_fake_zone("foo.foo", suffix="")
        self.assertFalse(f_c.purgeable)
        fqdn = "bar.x.y.z.foo.foo"
        label, the_domain = ensure_label_domain(fqdn)
        txt = TXT(label=label, domain=the_domain, txt_data="Nthing")
        txt.save()

        self.assertTrue(the_domain.purgeable)
        # txt makes the domain un-purgeable.
        self.assertFalse(prune_tree(the_domain))
        txt.delete()
        # The tree should have pruned itself

        # Make sure stuff was deleted.
        self.assertFalse(Domain.objects.filter(name="x.y.z.foo.foo"))
        self.assertFalse(Domain.objects.filter(name="y.z.foo.foo"))
        self.assertFalse(Domain.objects.filter(name="z.foo.foo"))
        self.assertTrue(Domain.objects.filter(name="foo.foo"))

    def test_basic_add_remove4(self):
        # Move a record down the tree testing prune's ability to not delete
        # stuff.
        f_c = create_fake_zone("foo.goo", suffix="")
        self.assertFalse(f_c.purgeable)
        fqdn = "bar.x.y.z.foo.goo"
        label, the_domain = ensure_label_domain(fqdn)
        txt = TXT(label=label, domain=the_domain, txt_data="Nthing")
        txt.save()

        self.assertTrue(the_domain.purgeable)

        # txt makes the domain un-purgeable.
        self.assertFalse(prune_tree(the_domain))
        txt.domain = the_domain.master_domain
        the_next_domain = the_domain.master_domain
        txt.save()
        self.assertFalse(Domain.objects.filter(pk=the_domain.pk))
        # We should be able to delete now.
        self.assertTrue(prune_tree(the_domain))
        the_domain = the_next_domain

        # txt makes the domain un-purgeable. y.z.foo.com
        self.assertFalse(prune_tree(the_domain))
        txt.domain = the_domain.master_domain
        the_next_domain = the_domain.master_domain
        txt.save()
        self.assertFalse(Domain.objects.filter(pk=the_domain.pk))
        # We should be able to delete now.
        the_domain = the_next_domain

        # txt makes the domain un-purgeable. z.foo.com
        self.assertFalse(prune_tree(the_domain))
        txt.domain = the_domain.master_domain
        the_next_domain = the_domain.master_domain
        txt.save()
        self.assertFalse(Domain.objects.filter(pk=the_domain.pk))
        # We should be able to delete now.
        the_domain = the_next_domain

        # txt makes the domain un-purgeable. foo.com
        self.assertFalse(prune_tree(the_domain))

    def test_basic_add_remove5(self):
        # Make sure all record types block
        f_c = create_fake_zone("foo.foo22", suffix="")
        self.assertFalse(f_c.purgeable)
        fqdn = "bar.x.y.z.foo.foo22"
        label, the_domain = ensure_label_domain(fqdn)

        txt = TXT(label=label, domain=the_domain, txt_data="Nthing")
        txt.save()
        self.assertFalse(prune_tree(the_domain))
        txt.delete()

        label, the_domain = ensure_label_domain(fqdn)
        addr = AddressRecord(label=label, domain=the_domain,
                             ip_type='4', ip_str="10.2.3.4")
        addr.save()
        self.assertFalse(prune_tree(the_domain))
        addr.delete()

        label, the_domain = ensure_label_domain(fqdn)
        mx = MX(label=label, domain=the_domain, server="foo", priority=4)
        mx.save()
        self.assertFalse(prune_tree(the_domain))
        mx.delete()

        label, the_domain = ensure_label_domain(fqdn)
        ns = Nameserver(domain=the_domain, server="asdfasffoo")
        ns.save()
        self.assertFalse(prune_tree(the_domain))
        ns.delete()

        label, the_domain = ensure_label_domain(fqdn)
        srv = SRV(
            label='_' + label, domain=the_domain, target="foo", priority=4,
            weight=4, port=34)
        srv.save()
        self.assertFalse(prune_tree(the_domain))
        srv.delete()

    def test_basic_add_remove6(self):
        # Make sure CNAME record block
        f_c = create_fake_zone("foo.foo1", suffix="")
        f_c.save()
        self.assertFalse(f_c.purgeable)
        fqdn = "cname.x.y.z.foo.foo1"
        label, the_domain = ensure_label_domain(fqdn)

        cname = CNAME(label=label, domain=the_domain, target="foo")
        cname.save()
        self.assertFalse(prune_tree(the_domain))
        cname.delete()

    def test_basic_add_remove7(self):
        # try a star record
        f_c = create_fake_zone("foo.foo2", suffix="")
        f_c.save()
        self.assertFalse(f_c.purgeable)
        fqdn = "*.x.y.z.foo.foo2"
        label, the_domain = ensure_label_domain(fqdn)
        self.assertEqual('*', label)

        cname = CNAME(label=label, domain=the_domain, target="foo")
        cname.save()
        self.assertFalse(prune_tree(the_domain))
        cname.delete()

    def test_basic_add_remove8(self):
        # Make sure a record's label is changed to '' when a domain with the
        # same name as it's fqdn is created.
        f_c = create_fake_zone("foo.foo3", suffix="")
        f_c.save()
        self.assertFalse(f_c.purgeable)
        fqdn = "www.x.y.z.foo.foo3"
        label, the_domain = ensure_label_domain(fqdn)
        self.assertEqual('www', label)
        self.assertEqual('x.y.z.foo.foo3', the_domain.name)
        self.assertTrue(the_domain.pk)

        cname = CNAME(label=label, domain=the_domain, target="foo")
        cname.save()
        fqdn = "*.www.x.y.z.foo.foo3"
        label2, the_domain2 = ensure_label_domain(fqdn)
        cname = CNAME.objects.get(fqdn=cname.fqdn)
        self.assertEqual('', cname.label)
        self.assertEqual('www.x.y.z.foo.foo3', cname.domain.name)
        self.assertEqual('*', label2)
        self.assertEqual('www.x.y.z.foo.foo3', the_domain2.name)

    def test_basic_add_remove9(self):
        # Make sure all record types block
        f_c = create_fake_zone("foo.foo22", suffix="")
        self.assertFalse(f_c.purgeable)
        fqdn = "y.z.foo.foo22"
        label, the_domain = ensure_label_domain(fqdn)
        addr = AddressRecord(label=label, domain=the_domain,
                             ip_type='4', ip_str="10.2.3.4")
        addr.save()
        self.assertFalse(prune_tree(the_domain))

        f_c = create_fake_zone("y.z.foo.foo22", suffix="")
        self.assertFalse(f_c.purgeable)
