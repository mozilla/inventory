from django.db.models.fields.related import ForeignKey
from django.test import TestCase
from django.test.client import RequestFactory

from systems.models import (
    OperatingSystem, Allocation, SystemStatus, System
)

from core.registration.static.models import StaticReg

from bulk_action.views import bulk_import

from mozdns.tests.utils import create_fake_zone
from mozdns.view.models import View

import decimal


class BulkActionTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.operating_system = OperatingSystem.objects.create(
            name='foo', version='1.1'
        )
        self.system_status = SystemStatus.objects.create(
            status='production', color='burgandy', color_code='wtf?'
        )
        self.allocation = Allocation.objects.create(name='something')
        self.domain = create_fake_zone('foobar.mozilla.com', suffix='')
        self.rdomain = create_fake_zone('10.in-addr.arpa', suffix='')

    def get_field(self, obj, attr):
        if hasattr(obj.__class__, attr) and attr != 'pk':
            m_attr = getattr(obj.__class__, attr)
            if isinstance(m_attr.field, ForeignKey):
                return getattr(obj, attr).pk
            else:
                raise Exception("Really bad error")
        else:
            return getattr(obj, attr)

    def assertUpdated(self, hostname, data, obj):
        s_data = None
        for d in data:
            if d.get('hostname', None) == hostname:
                s_data = d
                break
        if not s_data:
            self.fail('No system with hostname {0} was found'.format(hostname))

        for attr, value in s_data.iteritems():
            if isinstance(value, list):
                continue  # Don't do embeded json blobs
            o_value = self.get_field(obj, attr)
            if isinstance(o_value, decimal.Decimal):
                o_value = str(o_value)
            self.assertEqual(
                value, o_value, "For '{0}' data dict saw "
                "'{1}' but object has '{2}'".format(attr, value, o_value)
            )

    def test_single_create(self):
        hostname = 'puppet1.foobar.mozilla.com'
        data = """
        [{{
          "asset_tag": "7349",
          "system_type": 4,
          "serial": "MXQ14901XV",
          "rack_order": "1.16",
          "hostname": "{hostname}",
          "patch_panel_port": "",
          "purchase_date": null,
          "warranty_start": null,
          "purchase_price": "1.0",
          "oob_ip": "10.8.0.25",
          "allocation": {allocation_pk},
          "warranty_end": null,
          "switch_ports": "    bsx-b09: Gi1/0/16, Gi2/0/16"
        }}]
        """.format(allocation_pk=self.allocation.pk, hostname=hostname)
        pre_count = System.objects.all().count()
        json_data, error = bulk_import(data)
        self.assertFalse(error)
        s = System.objects.get(hostname=hostname)
        post_count = System.objects.all().count()
        self.assertTrue(pre_count == post_count - 1)
        self.assertUpdated(hostname, json_data, s)

    def test_single_update(self):
        hostname = 'puppet2.foobar.mozilla.com'
        data = """
        [{{
          "asset_tag": "7349",
          "system_type": 4,
          "serial": "MXQ14901XV",
          "rack_order": "1.16",
          "hostname": "{hostname}",
          "patch_panel_port": "",
          "purchase_date": null,
          "warranty_start": null,
          "purchase_price": "1.0",
          "oob_ip": "10.8.0.25",
          "allocation": {allocation_pk},
          "warranty_end": null,
          "switch_ports": "    bsx-b09: Gi1/0/16, Gi2/0/16"
        }}]
        """.format(allocation_pk=self.allocation.pk, hostname=hostname)
        pre_count = System.objects.all().count()
        json_data, error = bulk_import(data)
        self.assertFalse(error)
        s = System.objects.get(hostname=hostname)
        post_count = System.objects.all().count()
        self.assertTrue(pre_count == post_count - 1)
        s = System.objects.get(pk=s.pk)
        self.assertUpdated(hostname, json_data, s)

        # We now have an object created and the blob has a 'pk'. try changing
        # the hostname.
        new_hostname = 'asdf' + hostname
        json_data[0]['hostname'] = new_hostname

        pre_count = System.objects.all().count()
        json_data, error = bulk_import(json_data, load_json=False)
        self.assertFalse(error)
        s = System.objects.get(hostname=new_hostname)
        post_count = System.objects.all().count()
        self.assertTrue(pre_count == post_count)
        s = System.objects.get(pk=s.pk)
        self.assertUpdated(new_hostname, json_data, s)

    def test_pk_in_new_objects(self):
        hostname = 'puppet3.foobar.mozilla.com'
        data = """
        [{{
          "asset_tag": "7349",
          "system_type": 4,
          "serial": "MXQ14901XV",
          "rack_order": "1.16",
          "hostname": "{hostname}",
          "patch_panel_port": "",
          "purchase_date": null,
          "warranty_start": null,
          "purchase_price": "1.0",
          "oob_ip": "10.8.0.25",
          "allocation": {allocation_pk},
          "warranty_end": null,
          "switch_ports": "    bsx-b09: Gi1/0/16, Gi2/0/16",
          "staticreg_set": [
            {{
              "description": "Migrated SREG",
              "views": 2,
              "system": 5046,
              "fqdn": "puppet1.private.phx1.mozilla.com",
              "ttl": null,
              "ip_type": "4",
              "pk": 11,
              "ip_str": "10.8.75.10"
            }}
          ]
        }}]
        """.format(allocation_pk=self.allocation.pk, hostname=hostname)
        blobs, error = bulk_import(data)
        self.assertFalse(blobs)
        self.assertTrue(error)

    def test_single_sreg_create(self):
        hostname = 'puppet5.foobar.mozilla.com'
        data = """
        [{{
          "asset_tag": "7349",
          "system_type": 4,
          "serial": "MXQ14901XV",
          "rack_order": "1.16",
          "hostname": "{hostname}",
          "patch_panel_port": "",
          "purchase_date": null,
          "warranty_start": null,
          "purchase_price": "1.0",
          "oob_ip": "10.8.0.25",
          "allocation": {allocation_pk},
          "warranty_end": null,
          "switch_ports": "    bsx-b09: Gi1/0/16, Gi2/0/16",
          "staticreg_set": [
            {{
              "description": "Migrated SREG",
              "views": [{private_view_pk}],
              "fqdn": "{hostname}",
              "ttl": null,
              "ip_type": "4",
              "ip_str": "10.8.75.10"
            }}
          ]
        }}]
        """.format(
            allocation_pk=self.allocation.pk, hostname=hostname,
            private_view_pk=View.objects.get(name='private').pk
        )
        blobs, error = bulk_import(data)
        self.assertFalse(error)
        self.assertTrue('pk' in blobs[0]['staticreg_set'][0])
        sreg = StaticReg.objects.get(pk=blobs[0]['staticreg_set'][0]['pk'])
        self.assertTrue(sreg)
        self.assertTrue(sreg.system)

    def test_single_sreg_update(self):
        hostname = 'puppet12.foobar.mozilla.com'
        data = """
        [{{
          "asset_tag": "7349",
          "system_type": 4,
          "serial": "MXQ14901XV",
          "rack_order": "1.16",
          "hostname": "{hostname}",
          "patch_panel_port": "",
          "purchase_date": null,
          "warranty_start": null,
          "purchase_price": "1.0",
          "oob_ip": "10.8.0.25",
          "allocation": {allocation_pk},
          "warranty_end": null,
          "switch_ports": "    bsx-b09: Gi1/0/16, Gi2/0/16",
          "staticreg_set": [
            {{
              "description": "Migrated SREG",
              "views": [{private_view_pk}],
              "fqdn": "{hostname}",
              "ttl": null,
              "ip_type": "4",
              "ip_str": "10.8.75.10"
            }}
          ]
        }}]
        """.format(
            allocation_pk=self.allocation.pk, hostname=hostname,
            private_view_pk=View.objects.get(name='private').pk
        )
        blobs, error = bulk_import(data)
        self.assertFalse(error)
        self.assertTrue('pk' in blobs[0]['staticreg_set'][0])
        sreg = StaticReg.objects.get(pk=blobs[0]['staticreg_set'][0]['pk'])
        self.assertTrue(sreg)
        self.assertTrue(sreg.system)

        # Change the views and ip address. Make sure the updates worked.
        new_ip = "10.8.75.11"
        blobs[0]['staticreg_set'][0]['ip_str'] = new_ip
        blobs[0]['staticreg_set'][0]['views'] = [
            View.objects.get(name='public').pk,
            View.objects.get(name='private').pk
        ]

        blobs, error = bulk_import(blobs, load_json=False)
        sreg = StaticReg.objects.get(pk=sreg.pk)
        self.assertTrue(sreg)
        self.assertEqual(new_ip, sreg.ip_str)
        self.assertEqual(2, sreg.views.all().count())
        self.assertTrue(sreg.system)

    def test_single_hw_create(self):
        hostname = 'puppet6.foobar.mozilla.com'
        data = """
        [{{
          "asset_tag": "7349",
          "system_type": 4,
          "serial": "MXQ14901XV",
          "rack_order": "1.16",
          "hostname": "{hostname}",
          "patch_panel_port": "",
          "purchase_date": null,
          "warranty_start": null,
          "purchase_price": "1.0",
          "oob_ip": "10.8.0.25",
          "allocation": {allocation_pk},
          "warranty_end": null,
          "switch_ports": "    bsx-b09: Gi1/0/16, Gi2/0/16",
          "staticreg_set": [
            {{
              "description": "Migrated SREG",
              "views": [{private_view_pk}],
              "fqdn": "{hostname}",
              "ttl": null,
              "ip_type": "4",
              "ip_str": "10.8.75.10",
              "hwadapter_set": [
                {{
                  "mac": "44:1E:A1:5C:01:B4",
                  "name": "nic1",
                  "enable_dhcp": true,
                  "description": null,
                  "keyvalue_set": [
                    {{
                      "key": "hostname",
                      "value": "{hostname}"
                    }},
                    {{
                      "key": "dhcp_scope",
                      "value": "phx1-vlan80"
                    }}
                  ]
                }}
              ]
            }}
          ]
        }}]
        """.format(
            allocation_pk=self.allocation.pk, hostname=hostname,
            private_view_pk=View.objects.get(name='private').pk
        )
        blobs, error = bulk_import(data)
        self.assertFalse(error)
        self.assertTrue('pk' in blobs[0]['staticreg_set'][0])
        sreg = StaticReg.objects.get(pk=blobs[0]['staticreg_set'][0]['pk'])
        self.assertTrue(sreg)
        self.assertTrue(sreg.system)
        self.assertEqual(1, sreg.hwadapter_set.all().count())
        hw = sreg.hwadapter_set.get(mac="44:1E:A1:5C:01:B4")
        self.assertEqual(2, hw.keyvalue_set.all().count())
        hw.keyvalue_set.get(key='hostname', value=hostname)
        hw.keyvalue_set.get(key='dhcp_scope', value='phx1-vlan80')

    def test_single_hw_update(self):
        hostname = 'puppet99.foobar.mozilla.com'
        data = """
        [{{
          "asset_tag": "7349",
          "system_type": 4,
          "serial": "MXQ14901XV",
          "rack_order": "1.16",
          "hostname": "{hostname}",
          "patch_panel_port": "",
          "purchase_date": null,
          "warranty_start": null,
          "purchase_price": "1.0",
          "oob_ip": "10.8.0.25",
          "allocation": {allocation_pk},
          "warranty_end": null,
          "switch_ports": "    bsx-b09: Gi1/0/16, Gi2/0/16",
          "staticreg_set": [
            {{
              "description": "Migrated SREG",
              "views": [{private_view_pk}],
              "fqdn": "{hostname}",
              "ttl": null,
              "ip_type": "4",
              "ip_str": "10.8.75.10",
              "hwadapter_set": [
                {{
                  "mac": "44:1E:A1:5C:01:B4",
                  "name": "nic1",
                  "enable_dhcp": true,
                  "description": null,
                  "keyvalue_set": [
                    {{
                      "key": "hostname",
                      "value": "{hostname}"
                    }},
                    {{
                      "key": "dhcp_scope",
                      "value": "phx1-vlan80"
                    }}
                  ]
                }}
              ]
            }}
          ]
        }}]
        """.format(
            allocation_pk=self.allocation.pk, hostname=hostname,
            private_view_pk=View.objects.get(name='private').pk
        )
        blobs, error = bulk_import(data)
        self.assertFalse(error)
        self.assertTrue('pk' in blobs[0]['staticreg_set'][0])
        sreg = StaticReg.objects.get(pk=blobs[0]['staticreg_set'][0]['pk'])
        hw = sreg.hwadapter_set.get(mac="44:1E:A1:5C:01:B4")
        kv = hw.keyvalue_set.get(key='hostname')
        self.assertTrue(sreg)
        self.assertTrue(sreg.system)
        self.assertEqual(1, sreg.hwadapter_set.all().count())

        # Change the mac, make things are saved
        new_hostname = 'asdfasdf' + hostname
        new_mac = "44:1E:A1:5C:01:99"
        blobs[0]['staticreg_set'][0]['hwadapter_set'][0]['mac'] = new_mac
        # Chage the hostname in the kv set too
        for kv in blobs[0]['staticreg_set'][0]['hwadapter_set'][0]['keyvalue_set']:  # noqa
            if kv['key'] == 'hostname':
                kv['value'] = new_hostname

        blobs, error = bulk_import(blobs, load_json=False)

        hw = hw.__class__.objects.get(pk=hw.pk)
        kv = hw.keyvalue_set.get(key='hostname')
        self.assertEqual(new_mac, hw.mac)
        self.assertEqual(new_hostname, kv.value)
