from django.core.exceptions import ValidationError
from django.test import TestCase

from mozdns.domain.models import Domain
from mozdns.utils import ensure_label_domain
from mozdns.soa.models import SOA
from mozdns.tests.utils import create_fake_zone
from mozdns.address_record.models import AddressRecord


class AutoCreateTests(TestCase):
    """
    These tests should cover zone insurance and delegation blocking.
    Purgeable Domains
    """
    def setUp(self):
        Domain.objects.all().delete()

    def test_delegation_block(self):
        s, _ = SOA.objects.get_or_create(primary="foo", contact="Foo",
                                         description="foo")
        c = Domain(name='com')
        c.soa = s
        c.save()
        self.assertFalse(c.purgeable)
        f_c = Domain(name='foo.com')
        f_c.delegated = True
        f_c.save()
        self.assertFalse(f_c.purgeable)
        self.assertTrue(f_c.delegated)

        fqdn = "z.baz.foo.com"
        self.assertRaises(ValidationError, ensure_label_domain, fqdn)

    def test_no_soa_block(self):
        fqdn = "baz.bar.foo.eu"
        self.assertRaises(ValidationError, ensure_label_domain, fqdn)
        c = Domain(name='eu')
        c.save()
        self.assertFalse(c.purgeable)
        f_c = Domain(name='foo.eu')
        f_c.save()
        self.assertFalse(f_c.purgeable)

        # Even with domains there, they aren't part of a zone and should so
        # creation should fail.
        self.assertRaises(ValidationError, ensure_label_domain, fqdn)

    def test_no_soa_block2(self):
        c = Domain(name='moo')
        c.save()
        f_c = Domain(name='foo.moo')
        f_c.save()
        s, _ = SOA.objects.get_or_create(primary="bar23", contact="Foo",
                                         description="bar")
        f_c.soa = s
        f_c.save()

        self.assertRaises(ValidationError, ensure_label_domain, "baz.moo")

    def test_extend_doesnt_touch(self):
        # When we create a new domain, ensure that things are not touched
        root_domain = create_fake_zone("foo.mozilla.com", suffix="")
        shouldnt_be_touched = AddressRecord.objects.create(
            label='', domain=root_domain, ip_str='10.0.0.1', ip_type='4'
        )
        # Extend the tree
        label, baz_domain = ensure_label_domain('bar.baz.foo.mozilla.com')

        AddressRecord.objects.create(
            label=label, domain=baz_domain, ip_str='10.0.0.1', ip_type='4'
        )

        # The update() call will bypass the save/clean method of AddressRecord
        # so the fqdn of the A will remain unchanged. If our tree extender
        # function is touching this record its label will be changed to ''.
        AddressRecord.objects.filter(pk=shouldnt_be_touched.pk).update(
            label='shouldnt be touched'
        )

        ensure_label_domain('wee.boo.bar.baz.foo.mozilla.com')

        self.assertEqual(
            'shouldnt be touched',
            AddressRecord.objects.get(pk=shouldnt_be_touched.pk).label
        )

    def test_extend_does_touch(self):
        # When we create a new domain, ensure that things are updated
        root_domain = create_fake_zone("foo.mozilla.com", suffix="")
        shouldnt_be_touched = AddressRecord.objects.create(
            label='baz', domain=root_domain, ip_str='10.0.0.1', ip_type='4'
        )

        AddressRecord.objects.filter(pk=shouldnt_be_touched.pk).update(
            label='shouldnt be touched'
        )
        # Extend the tree
        ensure_label_domain('bar.baz.foo.mozilla.com')

        self.assertEqual(
            '',
            AddressRecord.objects.get(pk=shouldnt_be_touched.pk).label
        )
