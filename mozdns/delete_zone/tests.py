from django.test import TestCase

from mozdns.domain.models import Domain
from mozdns.soa.models import SOA
from mozdns.tests.utils import create_fake_zone
from mozdns.delete_zone.utils import delete_zone_helper


class DeleteZoneTests(TestCase):
    def test_delete(self):
        root_domain = create_fake_zone('foo.mozilla.com', suffix="")
        domain_name = root_domain.name
        delete_zone_helper(domain_name)
        self.assertFalse(Domain.objects.filter(name__contains=domain_name))

    def test_delete_hanging_domain_1(self):
        # What happens when there is a domain hanging off the root_domain that
        # isn't in the zone
        root_domain = create_fake_zone('foo1.mozilla.com', suffix="")
        domain_name = root_domain.name
        hang_domain = Domain.objects.create(name='bar.foo1.mozilla.com')
        self.assertFalse(hang_domain.soa)
        in_domain = Domain.objects.create(
            name='baz.foo1.mozilla.com', soa=root_domain.soa
        )
        in_domain_name = in_domain.name

        self.assertTrue(root_domain.has_record_set())
        delete_zone_helper(domain_name)
        self.assertFalse(root_domain.has_record_set())

        self.assertFalse(Domain.objects.filter(name__contains=in_domain_name))
        self.assertTrue(Domain.objects.filter(name__contains=root_domain.name))
        self.assertTrue(Domain.objects.filter(name__contains=hang_domain.name))

    def test_delete_hanging_domain_2(self):
        # What happens when there is a domain hanging off the root_domain that
        # isn't in the zone
        root_domain = create_fake_zone('foo2.mozilla.com', suffix="")
        d1 = Domain.objects.create(
            name='bar.foo2.mozilla.com', soa=root_domain.soa
        )
        soa2 = SOA.objects.create(
            primary='foo.com', contact='foo', description='foo'
        )
        d2 = Domain.objects.create(name='baz.bar.foo2.mozilla.com', soa=soa2)

        root_domain_name = root_domain.name
        d1_domain_name = d1.name
        d2_domain_name = d2.name
        self.assertTrue(root_domain.has_record_set())
        delete_zone_helper(root_domain_name)
        self.assertFalse(root_domain.has_record_set())

        self.assertTrue(Domain.objects.get(name=root_domain_name))
        self.assertTrue(Domain.objects.get(name=d1_domain_name))
        d2 = Domain.objects.get(name=d2_domain_name)
        self.assertEquals(d2.soa, soa2)
