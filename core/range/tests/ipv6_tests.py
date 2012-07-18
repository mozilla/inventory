from django.test import TestCase
from django.core.exceptions import ValidationError

from mozdns.domain.models import Domain
from core.network.models import Network
from core.range.models import Range

import ipaddr
import pdb

class V6RangeTests(TestCase):

    def setUp(self):
        self.d = Domain(name="com")
        self.s = Network(network_str="1234:1234:1234::/16", ip_type='6')
        self.s.update_network()
        self.s.save()

        self.s1 = Network(network_str="1234:1134:1234::/32", ip_type='6')
        self.s1.update_network()
        self.s1.save()

        self.s2 = Network(network_str="fff::/4", ip_type='6')
        self.s2.update_network()
        self.s2.save()

        self.s3 = Network(network_str="ffff::/4", ip_type='6')
        self.s3.update_network()
        self.s3.save()

    def do_add(self, start_str, end_str, default_domain, network, rtype, ip_type):
        r = Range(start_str=start_str, end_str=end_str, network=network)
        r.__repr__()
        r.save()
        return r

    def test1_create(self):
        start_str = "1234:1234:1234:1::"
        end_str = "1234:1234:1234:1234:1234:1234::"
        default_domain = self.d
        network = self.s
        rtype = 's'
        ip_type = '6'

        kwargs = {'start_str':start_str, 'end_str':end_str, 'default_domain':default_domain,
                'network':network, 'rtype':rtype, 'ip_type':ip_type}
        self.do_add(**kwargs)

    def test2_create(self):
        start_str = "1234:1234:1234:1234::"
        end_str = "1234:1234:1235:1234:1234:1234::"
        default_domain = self.d
        network = self.s
        rtype = 's'
        ip_type = '6'

        kwargs = {'start_str':start_str, 'end_str':end_str, 'default_domain':default_domain,
                'network':network, 'rtype':rtype, 'ip_type':ip_type}
        self.do_add(**kwargs)

    def test3_create(self):
        start_str = "ffff:ffff:ffff:ffff:ffff:ffff:ffff:fff0"
        end_str = "ffff:ffff:ffff:ffff:ffff:ffff:ffff:fffe"
        default_domain = self.d
        network = self.s3
        rtype = 's'
        ip_type = '6'

        kwargs = {'start_str':start_str, 'end_str':end_str, 'default_domain':default_domain,
                'network':network, 'rtype':rtype, 'ip_type':ip_type}
        r = self.do_add(**kwargs)
        self.assertEqual(r.start_upper, 0xffffffffffffffff)
        self.assertEqual(r.start_lower, 0xfffffffffffffff0)
        self.assertEqual(r.end_upper, 0xffffffffffffffff)
        self.assertEqual(r.end_lower, 0xfffffffffffffffe)

    def test1_bad_create(self):
        # start == end
        start_str = "1234:1235:1234:1234::"
        end_str = "1234:1235:1234:1234::"
        default_domain = self.d
        network = self.s
        rtype = 's'
        ip_type = '6'

        kwargs = {'start_str':start_str, 'end_str':end_str, 'default_domain':default_domain,
                'network':network, 'rtype':rtype, 'ip_type':ip_type}
        self.assertRaises(ValidationError, self.do_add, **kwargs)

    def test2_bad_create(self):
        # start > end
        start_str = "1234:1235:1234:1235::"
        end_str = "1234:1235:1234:1234::"
        default_domain = self.d
        network = self.s
        rtype = 's'
        ip_type = '6'

        kwargs = {'start_str':start_str, 'end_str':end_str, 'default_domain':default_domain,
                'network':network, 'rtype':rtype, 'ip_type':ip_type}
        self.assertRaises(ValidationError, self.do_add, **kwargs)

    def test3_bad_create(self):
        # outside of network
        start_str = "2235:1235:1234:1233::"
        end_str = "2235:1235:1234:1234::"
        default_domain = self.d
        network = self.s
        rtype = 's'
        ip_type = '6'

        kwargs = {'start_str':start_str, 'end_str':end_str, 'default_domain':default_domain,
                'network':network, 'rtype':rtype, 'ip_type':ip_type}
        self.assertRaises(ValidationError, self.do_add, **kwargs)

    def test4_bad_create(self):
        # outside of network
        start_str = "1234:1234:1234:1::"
        end_str = "1234:1234:1234:1234:1234:1234::"
        default_domain = self.d
        network = self.s1
        rtype = 's'
        ip_type = '6'

        kwargs = {'start_str':start_str, 'end_str':end_str, 'default_domain':default_domain,
                'network':network, 'rtype':rtype, 'ip_type':ip_type}
        self.assertRaises(ValidationError, self.do_add, **kwargs)

    def test5_bad_create(self):
        # duplicate
        start_str = "1234:123e:1234:1234::"
        end_str = "1234:123e:1235:1234:1234:1234::"
        default_domain = self.d
        network = self.s
        rtype = 's'
        ip_type = '6'

        kwargs = {'start_str':start_str, 'end_str':end_str, 'default_domain':default_domain,
                'network':network, 'rtype':rtype, 'ip_type':ip_type}
        self.do_add(**kwargs)

        start_str = "1234:123e:1234:1234::"
        end_str = "1234:123e:1235:1234:1234:1234::"
        default_domain = self.d
        network = self.s
        rtype = 's'
        ip_type = '6'

        kwargs = {'start_str':start_str, 'end_str':end_str, 'default_domain':default_domain,
                'network':network, 'rtype':rtype, 'ip_type':ip_type}
        self.assertRaises(ValidationError, self.do_add, **kwargs)

    def test6_bad_create(self):
        # Partial overlap
        #start_str = "10.0.4.1"
        #end_str = "10.0.4.55"
        start_str = "fe:1::"
        end_str = "fe:1:4::"
        default_domain = self.d
        network = self.s2
        rtype = 's'
        ip_type = '6'

        kwargs = {'start_str':start_str, 'end_str':end_str, 'default_domain':default_domain,
                'network':network, 'rtype':rtype, 'ip_type':ip_type}

        self.do_add(**kwargs)

        #start_str = "10.0.4.1"
        #end_str = "10.0.4.30"
        start_str = "fe:1::"
        end_str = "fe:1:3::"
        default_domain = self.d
        network = self.s2
        rtype = 's'
        ip_type = '6'

        kwargs = {'start_str':start_str, 'end_str':end_str, 'default_domain':default_domain,
                'network':network, 'rtype':rtype, 'ip_type':ip_type}

        self.assertRaises(ValidationError, self.do_add, **kwargs)

    def test7_bad_create(self):
        # Partial overlap
        #start_str = "10.0.4.1"
        #end_str = "10.0.4.55"
        start_str = "fe1:1::"
        end_str = "fe1:1:3::"
        default_domain = self.d
        network = self.s2
        rtype = 's'
        ip_type = '6'

        kwargs = {'start_str':start_str, 'end_str':end_str, 'default_domain':default_domain,
                'network':network, 'rtype':rtype, 'ip_type':ip_type}
        self.do_add(**kwargs)

        #start_str = "10.0.4.1"
        #end_str = "10.0.4.56"
        start_str = "fe1:1::"
        end_str = "fe1:1:4::"
        default_domain = self.d
        network = self.s2
        rtype = 's'
        ip_type = '6'

        kwargs = {'start_str':start_str, 'end_str':end_str, 'default_domain':default_domain,
                'network':network, 'rtype':rtype, 'ip_type':ip_type}
        self.assertRaises(ValidationError, self.do_add, **kwargs)

    def test8_bad_create(self):
        # Full overlap
        #start_str = "10.0.4.1"
        #end_str = "10.0.4.55"
        start_str = "fe2:1::"
        end_str = "fe2:1:4::"
        default_domain = self.d
        network = self.s2
        rtype = 's'
        ip_type = '6'

        kwargs = {'start_str':start_str, 'end_str':end_str, 'default_domain':default_domain,
                'network':network, 'rtype':rtype, 'ip_type':ip_type}
        self.do_add(**kwargs)

        #start_str = "10.0.4.2"
        #end_str = "10.0.4.55"
        start_str = "fe2:1:2::"
        end_str = "fe2:1:4::"
        default_domain = self.d
        network = self.s2
        rtype = 's'
        ip_type = '6'

        kwargs = {'start_str':start_str, 'end_str':end_str, 'default_domain':default_domain,
                'network':network, 'rtype':rtype, 'ip_type':ip_type}
        self.assertRaises(ValidationError, self.do_add, **kwargs)

    def test9_bad_create(self):
        # Full overlap
        #start_str = "10.0.4.1"
        #end_str = "10.0.4.55"
        start_str = "fe3:1:1::"
        end_str = "fe3:1:4::"
        default_domain = self.d
        network = self.s2
        rtype = 's'
        ip_type = '6'

        kwargs = {'start_str':start_str, 'end_str':end_str, 'default_domain':default_domain,
                'network':network, 'rtype':rtype, 'ip_type':ip_type}
        self.do_add(**kwargs)

        #start_str = "10.0.4.2"
        #end_str = "10.0.4.54"
        start_str = "fe3:1:2::"
        end_str = "fe3:1:3::"
        default_domain = self.d
        network = self.s2
        rtype = 's'
        ip_type = '6'

        kwargs = {'start_str':start_str, 'end_str':end_str, 'default_domain':default_domain,
                'network':network, 'rtype':rtype, 'ip_type':ip_type}
        self.assertRaises(ValidationError, self.do_add, **kwargs)

    def test10_bad_create(self):
        # Duplicate add
        #start_str = "10.0.4.1"
        #end_str = "10.0.4.55"
        start_str = "fe5:1:1::"
        end_str = "fe5:1:55::"
        default_domain = self.d
        network = self.s2
        rtype = 's'
        ip_type = '6'

        kwargs = {'start_str':start_str, 'end_str':end_str, 'default_domain':default_domain,
                'network':network, 'rtype':rtype, 'ip_type':ip_type}
        self.do_add(**kwargs)

        #start_str = "10.0.5.2"
        #end_str = "10.0.5.56"
        start_str = "fe5:1:56::"
        end_str = "fe5:1:57::"
        default_domain = self.d
        network = self.s2
        rtype = 's'
        ip_type = '6'

        kwargs = {'start_str':start_str, 'end_str':end_str, 'default_domain':default_domain,
                'network':network, 'rtype':rtype, 'ip_type':ip_type}

        self.do_add(**kwargs)
        self.assertRaises(ValidationError, self.do_add, **kwargs)

    def test11_bad_create(self):
        # More overlap tests
        #start_str = "10.0.4.5"
        #end_str = "10.0.4.55"
        start_str = "fe6:4:5::"
        end_str = "fe6:4:55::"
        default_domain = self.d
        network = self.s2
        rtype = 's'
        ip_type = '6'

        kwargs = {'start_str':start_str, 'end_str':end_str, 'default_domain':default_domain,
                'network':network, 'rtype':rtype, 'ip_type':ip_type}
        self.do_add(**kwargs)

        #start_str = "10.0.4.60"
        #end_str = "10.0.4.63"
        start_str = "fe6:4:60::"
        end_str = "fe6:4:63::"
        default_domain = self.d
        network = self.s2
        rtype = 's'
        ip_type = '6'

        kwargs = {'start_str':start_str, 'end_str':end_str, 'default_domain':default_domain,
                'network':network, 'rtype':rtype, 'ip_type':ip_type}
        self.do_add(**kwargs)

        #start_str = "10.0.4.1"
        #end_str = "10.0.4.4"
        start_str = "fe6:4:1::"
        end_str = "fe6:4:4::"
        default_domain = self.d
        network = self.s2
        rtype = 's'
        ip_type = '6'

        kwargs = {'start_str':start_str, 'end_str':end_str, 'default_domain':default_domain,
                'network':network, 'rtype':rtype, 'ip_type':ip_type}
        self.do_add(**kwargs)

        #start_str = "10.0.4.2"
        #end_str = "10.0.4.54"
        start_str = "fe6:4:2::"
        end_str = "fe6:4:54::"
        default_domain = self.d
        network = self.s2
        rtype = 's'
        ip_type = '6'

        kwargs = {'start_str':start_str, 'end_str':end_str, 'default_domain':default_domain,
                'network':network, 'rtype':rtype, 'ip_type':ip_type}
        self.assertRaises(ValidationError, self.do_add, **kwargs)

    def test12_bad_create(self):
        # Update range to something outside of the subnet.
        #start_str = "10.0.4.5"
        #end_str = "10.0.4.55"
        start_str = "fe7:4:5::"
        end_str = "fe7:4:55::"
        default_domain = self.d
        network = self.s2
        rtype = 's'
        ip_type = '6'

        kwargs = {'start_str':start_str, 'end_str':end_str, 'default_domain':default_domain,
                'network':network, 'rtype':rtype, 'ip_type':ip_type}
        self.do_add(**kwargs)

        #start_str = "10.0.4.60"
        #end_str = "10.0.4.63"
        start_str = "fe7:4:60::"
        end_str = "fe7:4:63::"
        default_domain = self.d
        network = self.s2
        rtype = 's'
        ip_type = '6'

        kwargs = {'start_str':start_str, 'end_str':end_str, 'default_domain':default_domain,
                'network':network, 'rtype':rtype, 'ip_type':ip_type}
        self.do_add(**kwargs)

        #start_str = "10.0.4.1"
        #end_str = "10.0.4.4"
        start_str = "fe7:4:1::"
        end_str = "fe7:4:4::"
        default_domain = self.d
        network = self.s2
        rtype = 's'
        ip_type = '6'

        kwargs = {'start_str':start_str, 'end_str':end_str, 'default_domain':default_domain,
                'network':network, 'rtype':rtype, 'ip_type':ip_type}
        r = self.do_add(**kwargs)
        r.end_str = "ffff:ffff:ffff::"

        self.assertRaises(ValidationError, r.clean)

    def test13_bad_create(self):
        #start_str = "10.0.4.5"
        #end_str = "10.0.4.55"
        start_str = "fe8:4:5::"
        end_str = "fe8:4:55::"
        default_domain = self.d
        network = self.s2
        rtype = 's'
        ip_type = '6'

        kwargs = {'start_str':start_str, 'end_str':end_str, 'default_domain':default_domain,
                'network':network, 'rtype':rtype, 'ip_type':ip_type}
        self.do_add(**kwargs)
        self.assertRaises(ValidationError, self.do_add, **kwargs)
