from django.test import TestCase
from django.core.exceptions import ValidationError

from mozdns.domain.models import Domain
from core.network.models import Network
from core.range.models import Range
from core.interface.static_intr.models import StaticInterface
from systems.models import System

import pdb

class V4RangeTests(TestCase):

    def setUp(self):
        self.d = Domain(name="com")
        self.d.save()
        Domain(name="arpa").save()
        Domain(name="in-addr.arpa").save()
        Domain(name="10.in-addr.arpa").save()
        self.s = Network(network_str="10.0.0.0/16", ip_type='4')
        self.s.update_network()
        self.s.save()

        self.s1 = Network(network_str="10.2.1.0/24", ip_type='4')
        self.s1.update_network()
        self.s1.save()

    def do_add(self, start_str, end_str, default_domain, network, rtype, ip_type):
        r = Range(start_str=start_str, end_str=end_str, network=network)
        r.__repr__()
        r.save()
        return r

    def test1_create(self):
        start_str = "10.0.0.1"
        end_str = "10.0.0.55"
        default_domain = self.d
        network = self.s
        rtype = 's'
        ip_type = '4'

        kwargs = {'start_str':start_str, 'end_str':end_str, 'default_domain':default_domain,
                'network':network, 'rtype':rtype, 'ip_type':ip_type}
        self.do_add(**kwargs)

    def test2_create(self):
        start_str = "10.0.1.1"
        end_str = "10.0.1.55"
        default_domain = self.d
        network = self.s
        rtype = 's'
        ip_type = '4'

        kwargs = {'start_str':start_str, 'end_str':end_str, 'default_domain':default_domain,
                'network':network, 'rtype':rtype, 'ip_type':ip_type}
        self.do_add(**kwargs)

    def test1_bad_create(self):
        # start == end
        start_str = "10.0.0.0"
        end_str = "10.1.0.0"
        default_domain = self.d
        network = self.s
        rtype = 's'
        ip_type = '4'

        kwargs = {'start_str':start_str, 'end_str':end_str, 'default_domain':default_domain,
                'network':network, 'rtype':rtype, 'ip_type':ip_type}
        self.assertRaises(ValidationError, self.do_add, **kwargs)

    def test2_bad_create(self):
        # start > end
        start_str = "10.0.0.2"
        end_str = "10.0.0.1"
        default_domain = self.d
        network = self.s
        rtype = 's'
        ip_type = '4'

        kwargs = {'start_str':start_str, 'end_str':end_str, 'default_domain':default_domain,
                'network':network, 'rtype':rtype, 'ip_type':ip_type}
        self.assertRaises(ValidationError, self.do_add, **kwargs)

    def test3_bad_create(self):
        # outside of network
        start_str = "11.0.0.2"
        end_str = "10.0.0.88"
        default_domain = self.d
        network = self.s
        rtype = 's'
        ip_type = '4'

        kwargs = {'start_str':start_str, 'end_str':end_str, 'default_domain':default_domain,
                'network':network, 'rtype':rtype, 'ip_type':ip_type}
        self.assertRaises(ValidationError, self.do_add, **kwargs)

    def test4_bad_create(self):
        # outside of network
        start_str = "10.2.0.0"
        end_str = "10.2.1.88"
        default_domain = self.d
        network = self.s1
        rtype = 's'
        ip_type = '4'

        kwargs = {'start_str':start_str, 'end_str':end_str, 'default_domain':default_domain,
                'network':network, 'rtype':rtype, 'ip_type':ip_type}
        self.assertRaises(ValidationError, self.do_add, **kwargs)

    def test5_bad_create(self):
        # duplicate
        start_str = "10.0.4.1"
        end_str = "10.0.4.55"
        default_domain = self.d
        network = self.s
        rtype = 's'
        ip_type = '4'

        kwargs = {'start_str':start_str, 'end_str':end_str, 'default_domain':default_domain,
                'network':network, 'rtype':rtype, 'ip_type':ip_type}
        self.do_add(**kwargs)

        start_str = "10.0.4.1"
        end_str = "10.0.4.55"
        default_domain = self.d
        network = self.s
        rtype = 's'
        ip_type = '4'

        kwargs = {'start_str':start_str, 'end_str':end_str, 'default_domain':default_domain,
                'network':network, 'rtype':rtype, 'ip_type':ip_type}
        self.assertRaises(ValidationError, self.do_add, **kwargs)

    def test6_bad_create(self):
        # Partial overlap
        start_str = "10.0.4.1"
        end_str = "10.0.4.55"
        default_domain = self.d
        network = self.s
        rtype = 's'
        ip_type = '4'

        kwargs = {'start_str':start_str, 'end_str':end_str, 'default_domain':default_domain,
                'network':network, 'rtype':rtype, 'ip_type':ip_type}

        self.do_add(**kwargs)

        start_str = "10.0.4.1"
        end_str = "10.0.4.30"
        default_domain = self.d
        network = self.s
        rtype = 's'
        ip_type = '4'

        kwargs = {'start_str':start_str, 'end_str':end_str, 'default_domain':default_domain,
                'network':network, 'rtype':rtype, 'ip_type':ip_type}

        self.assertRaises(ValidationError, self.do_add, **kwargs)

    def test7_bad_create(self):
        # Partial overlap
        start_str = "10.0.4.1"
        end_str = "10.0.4.55"
        default_domain = self.d
        network = self.s
        rtype = 's'
        ip_type = '4'

        kwargs = {'start_str':start_str, 'end_str':end_str, 'default_domain':default_domain,
                'network':network, 'rtype':rtype, 'ip_type':ip_type}
        self.do_add(**kwargs)

        start_str = "10.0.4.1"
        end_str = "10.0.4.56"
        default_domain = self.d
        network = self.s
        rtype = 's'
        ip_type = '4'

        kwargs = {'start_str':start_str, 'end_str':end_str, 'default_domain':default_domain,
                'network':network, 'rtype':rtype, 'ip_type':ip_type}
        self.assertRaises(ValidationError, self.do_add, **kwargs)

    def test8_bad_create(self):
        # Full overlap
        start_str = "10.0.4.1"
        end_str = "10.0.4.55"
        default_domain = self.d
        network = self.s
        rtype = 's'
        ip_type = '4'

        kwargs = {'start_str':start_str, 'end_str':end_str, 'default_domain':default_domain,
                'network':network, 'rtype':rtype, 'ip_type':ip_type}
        self.do_add(**kwargs)

        start_str = "10.0.4.2"
        end_str = "10.0.4.55"
        default_domain = self.d
        network = self.s
        rtype = 's'
        ip_type = '4'

        kwargs = {'start_str':start_str, 'end_str':end_str, 'default_domain':default_domain,
                'network':network, 'rtype':rtype, 'ip_type':ip_type}
        self.assertRaises(ValidationError, self.do_add, **kwargs)

    def test9_bad_create(self):
        # Full overlap
        start_str = "10.0.4.1"
        end_str = "10.0.4.55"
        default_domain = self.d
        network = self.s
        rtype = 's'
        ip_type = '4'

        kwargs = {'start_str':start_str, 'end_str':end_str, 'default_domain':default_domain,
                'network':network, 'rtype':rtype, 'ip_type':ip_type}
        self.do_add(**kwargs)

        start_str = "10.0.4.2"
        end_str = "10.0.4.54"
        default_domain = self.d
        network = self.s
        rtype = 's'
        ip_type = '4'

        kwargs = {'start_str':start_str, 'end_str':end_str, 'default_domain':default_domain,
                'network':network, 'rtype':rtype, 'ip_type':ip_type}
        self.assertRaises(ValidationError, self.do_add, **kwargs)

    def test10_bad_create(self):
        # Duplicate add
        start_str = "10.0.4.1"
        end_str = "10.0.4.55"
        default_domain = self.d
        network = self.s
        rtype = 's'
        ip_type = '4'

        kwargs = {'start_str':start_str, 'end_str':end_str, 'default_domain':default_domain,
                'network':network, 'rtype':rtype, 'ip_type':ip_type}
        self.do_add(**kwargs)

        start_str = "10.0.5.2"
        end_str = "10.0.5.56"
        default_domain = self.d
        network = self.s
        rtype = 's'
        ip_type = '4'

        kwargs = {'start_str':start_str, 'end_str':end_str, 'default_domain':default_domain,
                'network':network, 'rtype':rtype, 'ip_type':ip_type}

        self.do_add(**kwargs)
        self.assertRaises(ValidationError, self.do_add, **kwargs)

    def test11_bad_create(self):
        # More overlap tests
        start_str = "10.0.4.5"
        end_str = "10.0.4.55"
        default_domain = self.d
        network = self.s
        rtype = 's'
        ip_type = '4'

        kwargs = {'start_str':start_str, 'end_str':end_str, 'default_domain':default_domain,
                'network':network, 'rtype':rtype, 'ip_type':ip_type}
        self.do_add(**kwargs)

        start_str = "10.0.4.60"
        end_str = "10.0.4.63"
        default_domain = self.d
        network = self.s
        rtype = 's'
        ip_type = '4'

        kwargs = {'start_str':start_str, 'end_str':end_str, 'default_domain':default_domain,
                'network':network, 'rtype':rtype, 'ip_type':ip_type}
        self.do_add(**kwargs)

        start_str = "10.0.4.1"
        end_str = "10.0.4.4"
        default_domain = self.d
        network = self.s
        rtype = 's'
        ip_type = '4'

        kwargs = {'start_str':start_str, 'end_str':end_str, 'default_domain':default_domain,
                'network':network, 'rtype':rtype, 'ip_type':ip_type}
        self.do_add(**kwargs)

        start_str = "10.0.4.2"
        end_str = "10.0.4.54"
        default_domain = self.d
        network = self.s
        rtype = 's'
        ip_type = '4'

        kwargs = {'start_str':start_str, 'end_str':end_str, 'default_domain':default_domain,
                'network':network, 'rtype':rtype, 'ip_type':ip_type}
        self.assertRaises(ValidationError, self.do_add, **kwargs)

    def test12_bad_create(self):
        # Update range to something outside of the subnet.
        start_str = "10.0.4.5"
        end_str = "10.0.4.55"
        default_domain = self.d
        network = self.s
        rtype = 's'
        ip_type = '4'

        kwargs = {'start_str':start_str, 'end_str':end_str, 'default_domain':default_domain,
                'network':network, 'rtype':rtype, 'ip_type':ip_type}
        self.do_add(**kwargs)

        start_str = "10.0.4.60"
        end_str = "10.0.4.63"
        default_domain = self.d
        network = self.s
        rtype = 's'
        ip_type = '4'

        kwargs = {'start_str':start_str, 'end_str':end_str, 'default_domain':default_domain,
                'network':network, 'rtype':rtype, 'ip_type':ip_type}
        self.do_add(**kwargs)

        start_str = "10.0.4.1"
        end_str = "10.0.4.4"
        default_domain = self.d
        network = self.s
        rtype = 's'
        ip_type = '4'

        kwargs = {'start_str':start_str, 'end_str':end_str, 'default_domain':default_domain,
                'network':network, 'rtype':rtype, 'ip_type':ip_type}
        r = self.do_add(**kwargs)
        r.end_str = "160.0.4.60"

        self.assertRaises(ValidationError, r.clean)

    def test13_bad_create(self):
        start_str = "10.0.4.5"
        end_str = "10.0.4.55"
        default_domain = self.d
        network = self.s
        rtype = 's'
        ip_type = '4'

        kwargs = {'start_str':start_str, 'end_str':end_str, 'default_domain':default_domain,
                'network':network, 'rtype':rtype, 'ip_type':ip_type}
        self.do_add(**kwargs)
        self.assertRaises(ValidationError, self.do_add, **kwargs)

    def test1_freeip(self):
        start_str = "10.0.33.1"
        end_str = "10.0.33.3"
        default_domain = self.d
        network = self.s
        rtype = 's'
        ip_type = '4'
        system = System()

        kwargs = {'start_str':start_str, 'end_str':end_str, 'default_domain':default_domain,
                'network':network, 'rtype':rtype, 'ip_type':ip_type}
        r = self.do_add(**kwargs)
        self.assertEqual(str(r.get_next_ip()), "10.0.33.1")
        self.assertEqual(str(r.get_next_ip()), "10.0.33.1")
        s = StaticInterface(label="foo", domain=self.d, ip_type='4',
                ip_str=str(r.get_next_ip()), system=system,
                mac="00:00:00:00:00:00")
        s.clean()
        s.save()
        self.assertEqual(str(r.get_next_ip()), "10.0.33.2")
        s = StaticInterface(label="foo", domain=self.d, ip_type='4',
                ip_str=str(r.get_next_ip()), system=system,
                mac="00:00:00:00:00:00")
        s.clean()
        s.save()
        self.assertEqual(str(r.get_next_ip()), "10.0.33.3")
        s = StaticInterface(label="foo", domain=self.d, ip_type='4',
                ip_str=str(r.get_next_ip()), system=system,
                mac="00:00:00:00:00:00")
        s.clean()
        s.save()
        self.assertEqual(r.get_next_ip(), None)
