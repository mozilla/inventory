from django.db.models.fields.related import ForeignKey
from django.test import TestCase
from django.test.client import RequestFactory

from systems.models import (
    OperatingSystem, Allocation, SystemStatus, System
)

from bulk_action.views import bulk_import

"""
{
      "asset_tag": "7349",
      "system_type": 4,
      "serial": "MXQ14901XV",
      "rack_order": 1.16,
      "hostname": "puppet1.private.phx1.mozilla.com",
      "patch_panel_port": "",
      "purchase_date": null,
      "pk": 5046,
      "warranty_start": null,
      "purchase_price": "1.0",
      "oob_ip": "10.8.0.25",
      "allocation": 1,
      "warranty_end": null,
      "switch_ports": "    bsx-b09: Gi1/0/16, Gi2/0/16",
      "static_reg_set": [
        {
          "description": "Migrated SREG",
          "views": 2,
          "system": 5046,
          "fqdn": "puppet1.private.phx1.mozilla.com",
          "ttl": null,
          "hwadapter_set": [
            {
              "description": null,
              "enable_dhcp": true,
              "sreg": 11,
              "mac": "44:1E:A1:5C:01:B4",
              "pk": 27,
              "name": "nic1"
            },
            {
              "description": null,
              "enable_dhcp": true,
              "sreg": 11,
              "mac": "44:1E:A1:5C:01:B0",
              "pk": 28,
              "name": "nic0"
            }
          ],
          "ip_type": "4",
          "pk": 11,
          "ip_str": "10.8.75.10"
        },
        {
          "description": "",
          "views": 2,
          "system": 5046,
          "fqdn": "puppet1.private.phx1.mozilla.com",
          "ttl": null,
          "hwadapter_set": [
            {
              "description": "",
              "enable_dhcp": true,
              "sreg": 12,
              "mac": "11:22:33:44:55:66",
              "pk": 29,
              "name": "nic1"
            }
          ],
          "ip_type": "4",
          "pk": 12,
          "ip_str": "10.8.75.212"
        }
      ],
      "system_rack": 72,
      "operating_system": 47,
      "notes": "",
      "oob_switch_port": "",
      "server_model": 353,
      "system_status": 1,
      "change_password": null
    }
"""


class OncallTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.operating_system = OperatingSystem.objects.create(
            name='foo', version='1.1'
        )
        self.system_status = SystemStatus.objects.create(
            status='production', color='burgandy', color_code='wtf?'
        )
        self.allocation = Allocation.objects.create(name='something')

    def get_field(self, obj, attr):
        if hasattr(obj.__class__, attr):
            m_attr = getattr(obj.__class__, attr)
            if isinstance(m_attr.field, ForeignKey):
                return getattr(obj, attr).pk
            else:
                raise Exception("Really bad error")
        else:
            return getattr(obj, attr)

    def assertUpdated(self, data, obj):
        for attr, value in data.iteritems():
            if isinstance(value, list):
                continue  # Don't do embeded json blobs
            o_value = self.get_field(obj, attr)
            self.assertEqual(
                value, o_value, "For '{0}' data dict saw "
                "'{1}' but object has '{2}'".format(attr, value, o_value)
            )

    def test_simple_create(self):
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
        json_data = bulk_import(data)
        s = System.objects.get(hostname=hostname)
        #import pdb;pdb.set_trace()
        # need to introspect on the list to pull out the system with the
        # same hostname
        self.assertUpdated(json_data, s)
