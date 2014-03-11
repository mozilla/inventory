from django.core.urlresolvers import reverse
from django.test import Client
from django.test import TestCase

from core.range.models import Range
from core.network.models import Network
from core.site.models import Site
from core.vlan.models import Vlan
from core.range.ip_choosing_utils import (
    calc_template_ranges, integrate_real_ranges
)

import ipaddr
import simplejson as json


class ChooserOverlapTests(TestCase):
    def setUp(self):
        self.n1 = Network.objects.create(
            network_str='10.8.0.0/24', ip_type='4'
        )

    def test_contained_in_template(self):
        # 1 to 15 is templated to be special purpose
        r1 = Range.objects.create(
            start_str='10.8.0.2', end_str='10.8.0.14', network=self.n1
        )
        trs = calc_template_ranges(self.n1)
        rs = integrate_real_ranges(self.n1, trs)
        self.assertEqual(len(rs), len(trs))
        rs = sorted(rs, key=lambda r: int(ipaddr.IPv4Address(r['start'])))

        self.assertEqual(r1.start_str, rs[0]['start'])
        self.assertEqual(r1.end_str, rs[0]['end'])
        self.assertEqual(r1.pk, rs[0]['pk'])

    def test_not_in_template(self):
        # 1 to 15 is templated to be special purpose
        r1 = Range.objects.create(
            start_str='10.8.0.2', end_str='10.8.0.14', network=self.n1
        )
        trs = calc_template_ranges(self.n1)
        trs = sorted(trs, key=lambda r: int(ipaddr.IPv4Address(r['start'])))

        # remove the first range that would have conflicted
        trs.pop(0)

        rs = integrate_real_ranges(self.n1, trs)
        rs = sorted(rs, key=lambda r: int(ipaddr.IPv4Address(r['start'])))

        self.assertEqual(r1.start_str, rs[0]['start'])
        self.assertEqual(r1.end_str, rs[0]['end'])
        self.assertEqual(r1.pk, rs[0]['pk'])

    def test_overlaps_two_ranges(self):
        # 1 to 15 is templated to be special purpose
        # 16 to 127 is templated to be multi-host pools
        r1 = Range.objects.create(
            start_str='10.8.0.10', end_str='10.8.0.100', network=self.n1
        )

        trs = calc_template_ranges(self.n1)
        n_trs = len(trs)
        rs = integrate_real_ranges(self.n1, trs)
        # We should have lost one range
        self.assertEqual(n_trs - 1, len(rs))
        rs = sorted(rs, key=lambda r: int(ipaddr.IPv4Address(r['start'])))

        self.assertEqual(r1.start_str, rs[0]['start'])
        self.assertEqual(r1.end_str, rs[0]['end'])
        self.assertEqual(r1.pk, rs[0]['pk'])


class ChooserTests(TestCase):
    def setUp(self):
        """
        We need to setup a realistic set of objects to test the related engine

        sites = s1  s2  s3
        vlans = v1  v2  v3
        networks = n1 n2 n3 n4 n5

        Site Relationships:
        n1 -> s1
        n2 -> s1
        n3 -> s3
        n4 -> s2
        n5 -> s2
        n6 -> None
        n7 -> s2
        n8 -> None

        Vlan Relationships:
        n1 -> v1
        n2 -> v1
        n3 -> v2
        n4 -> v3
        n5 -> v3
        n6 -> v3
        n7 -> None
        n8 -> None
        """
        self.client = Client()
        #sites = s1  s2  s3
        self.s1 = Site.objects.create(full_name="s1")
        self.s2 = Site.objects.create(full_name="s2")
        self.s3 = Site.objects.create(full_name="s3")

        #vlans = v1  v2  v3
        self.v1 = Vlan.objects.create(name="v1", number=1)
        self.v2 = Vlan.objects.create(name="v2", number=2)
        self.v3 = Vlan.objects.create(name="v3", number=3)

        #networks = n1 n2 n3 n4 n5

        #Relationships:
        n_t = "10.0.{0}.0/24"  # network_str template
        #n1 -> s1
        #n1 -> v1
        self.n1 = Network.objects.create(
            network_str=n_t.format(1), site=self.s1, vlan=self.v1, ip_type='4'
        )

        #n2 -> s1
        #n2 -> v1
        self.n2 = Network.objects.create(
            network_str=n_t.format(2), site=self.s2, vlan=self.v2, ip_type='4'
        )

        #n3 -> s3
        #n3 -> v2
        self.n3 = Network.objects.create(
            network_str=n_t.format(3), site=self.s3, vlan=self.v2, ip_type='4'
        )

        #n4 -> s2
        #n4 -> v3
        self.n4 = Network.objects.create(
            network_str=n_t.format(4), site=self.s2, vlan=self.v3, ip_type='4'
        )

        #n5 -> s2
        #n5 -> v3
        self.n5 = Network.objects.create(
            network_str=n_t.format(5), site=self.s2, vlan=self.v3, ip_type='4'
        )

        #n6 -> None
        #n6 -> v3
        self.n6 = Network.objects.create(
            network_str=n_t.format(6), site=None, vlan=self.v3, ip_type='4'
        )

        #n7 -> s2
        #n7 -> None
        self.n7 = Network.objects.create(
            network_str=n_t.format(7), site=self.s2, vlan=None, ip_type='4'
        )

        #n8 -> None
        #n8 -> None
        self.n8 = Network.objects.create(
            network_str=n_t.format(8), site=None, vlan=None, ip_type='4'
        )

    def test_one_site(self):
        state = {
            'networks': [],
            'sites': [self.s1.pk],
            'vlans': [],
        }

        state['choice'] = ['site', self.s1.pk]

        resp = self.client.post(
            '/en-US' + reverse('find-related'),
            json.dumps(state),
            content_type='application/json'
        )
        self.assertEqual(200, resp.status_code)
        r = json.loads(resp.content)
        self.assertEqual(1, len(r['sites']))
        self.assertEqual(self.s1.pk, r['sites'][0]['value'])
        self.assertEqual(0, len(r['vlans']))
        self.assertEqual(0, len(r['networks']))

    def test_two_sites(self):
        state = {
            'networks': [],
            'sites': [self.s1.pk, self.s2.pk],
            'vlans': [],
        }

        state['choice'] = ['site', self.s1.pk]

        resp = self.client.post(
            '/en-US' + reverse('find-related'),
            json.dumps(state),
            content_type='application/json'
        )
        self.assertEqual(200, resp.status_code)
        r = json.loads(resp.content)
        self.assertEqual(1, len(r['sites']))
        self.assertEqual(self.s1.pk, r['sites'][0]['value'])
        self.assertEqual(0, len(r['vlans']))
        self.assertEqual(0, len(r['networks']))

    def test_two_sites_un_related_net(self):
        state = {
            'networks': [self.n3.pk],
            'sites': [self.s1.pk, self.s2.pk],
            'vlans': [],
        }

        state['choice'] = ['site', self.s1.pk]

        resp = self.client.post(
            '/en-US' + reverse('find-related'),
            json.dumps(state),
            content_type='application/json'
        )
        self.assertEqual(200, resp.status_code)
        r = json.loads(resp.content)
        self.assertEqual(1, len(r['sites']))
        self.assertEqual(self.s1.pk, r['sites'][0]['value'])
        self.assertEqual(0, len(r['vlans']))
        self.assertEqual(0, len(r['networks']))

    def test_two_sites_un_related_nets_and_vlans(self):
        state = {
            'networks': [self.n3.pk, self.n4.pk],
            'sites': [self.s1.pk, self.s2.pk],
            'vlans': [self.n3.vlan.pk, self.n4.vlan.pk],
        }

        state['choice'] = ['site', self.s1.pk]

        resp = self.client.post(
            '/en-US' + reverse('find-related'),
            json.dumps(state),
            content_type='application/json'
        )
        self.assertEqual(200, resp.status_code)
        r = json.loads(resp.content)
        self.assertEqual(1, len(r['sites']))
        self.assertEqual(self.s1.pk, r['sites'][0]['value'])
        self.assertEqual(0, len(r['vlans']))
        self.assertEqual(0, len(r['networks']))

    def test_related_site_network_vlan(self):
        n = self.s1.network_set.all()[0]
        state = {
            'networks': [n.pk],
            'sites': [self.s1.pk],
            'vlans': [n.vlan.pk]
        }

        state['choice'] = ['site', self.s1.pk]

        resp = self.client.post(
            '/en-US' + reverse('find-related'),
            json.dumps(state),
            content_type='application/json'
        )
        self.assertEqual(200, resp.status_code)
        r = json.loads(resp.content)
        self.assertEqual(1, len(r['networks']))
        self.assertEqual(n.pk, r['networks'][0]['value'])

        self.assertEqual(1, len(r['sites']))
        self.assertEqual(self.s1.pk, r['sites'][0]['value'])

        self.assertEqual(1, len(r['vlans']))
        self.assertEqual(n.vlan.pk, r['vlans'][0]['value'])

    def test_related_site_network_vlan_with_unrelated_objects(self):
        state = {
            'networks': [self.n1.pk, self.n4.pk],
            'sites': [self.s1.pk, self.s2.pk],
            'vlans': [self.n1.vlan.pk]
        }

        state['choice'] = ['site', self.s1.pk]

        resp = self.client.post(
            '/en-US' + reverse('find-related'),
            json.dumps(state),
            content_type='application/json'
        )
        self.assertEqual(200, resp.status_code)
        r = json.loads(resp.content)
        self.assertEqual(1, len(r['networks']))
        self.assertEqual(self.n1.pk, r['networks'][0]['value'])

        self.assertEqual(1, len(r['sites']))
        self.assertEqual(self.s1.pk, r['sites'][0]['value'])

        self.assertEqual(1, len(r['vlans']))
        self.assertEqual(self.n1.vlan.pk, r['vlans'][0]['value'])

    def test_choose_network_with_no_site(self):
        state = {
            'networks': [self.n6.pk],
            'sites': [self.s1.pk, self.s2.pk],
            'vlans': [self.n6.vlan.pk]
        }

        state['choice'] = ['network', self.n6.pk]

        resp = self.client.post(
            '/en-US' + reverse('find-related'),
            json.dumps(state),
            content_type='application/json'
        )
        self.assertEqual(200, resp.status_code)
        r = json.loads(resp.content)
        self.assertEqual(1, len(r['networks']))
        self.assertEqual(self.n6.pk, r['networks'][0]['value'])

        self.assertEqual(0, len(r['sites']))

        self.assertEqual(1, len(r['vlans']))
        self.assertEqual(self.n6.vlan.pk, r['vlans'][0]['value'])

    def test_choose_network_with_no_site_no_vlan(self):
        state = {
            'networks': [self.n8.pk],
            'sites': [self.s1.pk, self.s2.pk],
            'vlans': [self.n6.vlan.pk]
        }

        state['choice'] = ['network', self.n8.pk]

        resp = self.client.post(
            '/en-US' + reverse('find-related'),
            json.dumps(state),
            content_type='application/json'
        )
        self.assertEqual(200, resp.status_code)
        r = json.loads(resp.content)
        self.assertEqual(1, len(r['networks']))
        self.assertEqual(self.n8.pk, r['networks'][0]['value'])

        self.assertEqual(0, len(r['sites']))
        self.assertEqual(0, len(r['vlans']))

    def test_related_site_network_vlan_multiple_choices(self):
        state = {
            'networks': [self.n1.pk, self.n3.pk],
            'sites': [self.n1.site.pk, self.n3.site.pk],
            'vlans': [self.n1.vlan.pk, self.n3.vlan.pk]
        }

        state['choice'] = ['site', self.s1.pk]

        resp = self.client.post(
            '/en-US' + reverse('find-related'),
            json.dumps(state),
            content_type='application/json'
        )
        self.assertEqual(200, resp.status_code)
        new_state = json.loads(resp.content)
        self.assertEqual(1, len(new_state['networks']))
        self.assertEqual(self.n1.pk, new_state['networks'][0]['value'])

        self.assertEqual(1, len(new_state['sites']))
        self.assertEqual(self.n1.site.pk, new_state['sites'][0]['value'])

        self.assertEqual(1, len(new_state['vlans']))
        self.assertEqual(self.n1.vlan.pk, new_state['vlans'][0]['value'])

        # Make another choice
        new_state['choice'] = ['vlan', self.n1.vlan.pk]
        self.assertEqual(1, len(new_state['networks']))
        self.assertEqual(self.n1.pk, new_state['networks'][0]['value'])

        self.assertEqual(1, len(new_state['sites']))
        self.assertEqual(self.n1.site.pk, new_state['sites'][0]['value'])

        self.assertEqual(1, len(new_state['vlans']))
        self.assertEqual(self.n1.vlan.pk, new_state['vlans'][0]['value'])
