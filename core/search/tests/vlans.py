from django.test import TestCase

from mozdns.tests.utils import create_fake_zone
from mozdns.ptr.models import PTR
from mozdns.address_record.models import AddressRecord
from core.search.compiler.django_compile import compile_to_django
from core.vlan.models import Vlan
from core.network.models import Network


class VLANTests(TestCase):

    def test_integration5_ip(self):
        root_domain = create_fake_zone("wee5.wee.mozilla.com", "")
        create_fake_zone("10.in-addr.arpa", "")
        res, error = compile_to_django("10.in-addr.arpa OR "
                                       "wee5.wee.mozilla.com")
        self.assertFalse(error)
        self.assertEqual(len(res['SOA']), 2)
        self.assertEqual(len(res['NS']), 2)
        self.assertEqual(len(res['DOMAIN']), 2)
        PTR.objects.create(
            name="host1.wee2.wee.mozilla.com", ip_str="10.0.0.1", ip_type="4"
        )
        AddressRecord.objects.create(
            label="host1", domain=root_domain, ip_str="10.0.0.1", ip_type="4"
        )

        PTR.objects.create(
            name="host2.wee2.wee.mozilla.com", ip_str="10.0.0.5", ip_type="4"
        )
        AddressRecord.objects.create(
            label="host2", domain=root_domain, ip_str="10.0.0.5", ip_type="4"
        )

        vlan1 = Vlan.objects.create(name='vlan-foo', number=1)
        vlan2 = Vlan.objects.create(name='vlan-foo', number=2)
        net1 = Network.objects.create(network_str='10.0.0.0/30', ip_type='4')
        net2 = Network.objects.create(network_str='10.0.0.4/30', ip_type='4')

        # Don't associate networks and vlans yet
        res, error = compile_to_django('vlan=:vlan-foo')
        self.assertFalse(error)
        self.assertEqual(len(res['PTR']), 0)
        self.assertEqual(len(res['A']), 0)

        res, error = compile_to_django('vlan=:vlan-foo,1')
        self.assertFalse(error)
        self.assertEqual(len(res['PTR']), 0)
        self.assertEqual(len(res['A']), 0)

        res, error = compile_to_django('vlan=:1,vlan-foo')
        self.assertFalse(error)
        self.assertEqual(len(res['PTR']), 0)
        self.assertEqual(len(res['A']), 0)

        net1.vlan = vlan1
        net1.save()

        net2.vlan = vlan2
        net2.save()

        res, error = compile_to_django('vlan=:vlan-foo')
        self.assertFalse(error)
        self.assertEqual(len(res['PTR']), 2)
        self.assertEqual(len(res['A']), 2)

        res, error = compile_to_django('vlan=:vlan-foo,1')
        self.assertFalse(error)
        self.assertEqual(len(res['PTR']), 1)
        self.assertEqual(len(res['A']), 1)

        res, error = compile_to_django('vlan=:1,vlan-foo')
        self.assertFalse(error)
        self.assertEqual(len(res['PTR']), 1)
        self.assertEqual(len(res['A']), 1)

        res, error = compile_to_django('vlan=:vlan-foo,2')
        self.assertFalse(error)
        self.assertEqual(len(res['PTR']), 1)
        self.assertEqual(len(res['A']), 1)

        res, error = compile_to_django('vlan=:2,vlan-foo')
        self.assertFalse(error)
        self.assertEqual(len(res['PTR']), 1)
        self.assertEqual(len(res['A']), 1)

        res, error = compile_to_django('vlan=:1')
        self.assertFalse(error)
        self.assertEqual(len(res['PTR']), 1)
        self.assertEqual(len(res['A']), 1)

        vlan2.name = 'vlan-bar'
        vlan2.save()

        res, error = compile_to_django('vlan=:vlan-foo')
        self.assertFalse(error)
        self.assertEqual(len(res['PTR']), 1)
        self.assertEqual(len(res['A']), 1)
