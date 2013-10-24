from django.db.models.fields.related import ForeignKey
#from django.test import TransactionTestCase as TestCase
from django.test import TestCase
from django.test.client import RequestFactory

from systems.models import (
    OperatingSystem, Allocation, SystemStatus, System
)

from core.registration.static.models import StaticReg

from bulk_action.views import bulk_import

from mozdns.cname.models import CNAME
from mozdns.tests.utils import create_fake_zone
from mozdns.view.models import View

import decimal


class BulkActionTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.private_view = View.objects.create(name='private')
        self.operating_system = OperatingSystem.objects.create(
            name='foo', version='1.1'
        )
        self.system_status = SystemStatus.objects.create(
            status='production', color='burgandy', color_code='wtf?'
        )
        self.allocation = Allocation.objects.create(name='something')
        self.domain = create_fake_zone('foobar.mozilla.com', suffix='')
        self.build_domain = create_fake_zone('build.mozilla.org', suffix='')
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
        for d in data['systems'].values():
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
        {{
            "systems": {{
                "{hostname}": {{
                    "asset_tag": "7349",
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
                }}
            }}
        }}
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
        {{
            "systems": {{
                "{hostname}": {{
                    "asset_tag": "7349",
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
                }}
            }}
        }}
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
        json_data['systems'][hostname]['hostname'] = new_hostname

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
        {{
            "systems": {{
                "{hostname}": {{
                    "asset_tag": "7349",
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
                    "staticreg_set": {{
                        "nic0": {{
                            "description": "Migrated SREG",
                            "views": [{private_view_pk}],
                            "system": 5046,
                            "fqdn": "puppet1.private.phx1.mozilla.com",
                            "ttl": null,
                            "ip_type": "4",
                            "pk": 11,
                            "ip_str": "10.8.75.10"
                        }}
                    }}
                }}
            }}
        }}
        """.format(
            allocation_pk=self.allocation.pk, hostname=hostname,
            private_view_pk=self.private_view.pk
        )
        blobs, error = bulk_import(data)
        self.assertFalse(blobs)
        self.assertTrue(error)

    def test_single_sreg_create(self):
        hostname = 'puppet5.foobar.mozilla.com'
        data = """
        {{
            "systems": {{
                "{hostname}": {{
                    "asset_tag": "7349",
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
                    "staticreg_set": {{
                        "nic0": {{
                            "description": "Migrated SREG",
                            "views": [{private_view_pk}],
                            "fqdn": "{hostname}",
                            "ttl": null,
                            "ip_type": "4",
                            "ip_str": "10.8.75.10"
                        }}
                    }}
                }}
            }}
        }}
        """.format(
            allocation_pk=self.allocation.pk, hostname=hostname,
            private_view_pk=self.private_view.pk
        )
        blobs, error = bulk_import(data)
        self.assertFalse(error)
        self.assertTrue(
            'pk' in blobs['systems'][hostname]['staticreg_set']['nic0']
        )
        sreg = StaticReg.objects.get(
            pk=blobs['systems'][hostname]['staticreg_set']['nic0']['pk']
        )
        self.assertTrue(sreg)
        self.assertTrue(sreg.system)
        self.assertTrue(sreg.views.filter(name='private'))
        self.assertEqual(1, len(sreg.views.all()))

    def test_single_sreg_update(self):
        hostname = 'puppet12.foobar.mozilla.com'
        data = """
        {{
            "systems": {{
                "{hostname}": {{
                    "asset_tag": "7349",
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
                    "staticreg_set": {{
                        "nic1": {{
                            "description": "Migrated SREG",
                            "views": [{private_view_pk}],
                            "fqdn": "{hostname}",
                            "ttl": null,
                            "ip_type": "4",
                            "ip_str": "10.8.75.10"
                        }}
                    }}
                }}
            }}
        }}
        """.format(
            allocation_pk=self.allocation.pk, hostname=hostname,
            private_view_pk=View.objects.get(name='private').pk
        )
        blobs, error = bulk_import(data)
        self.assertFalse(error)
        self.assertTrue(
            'pk' in blobs['systems'][hostname]['staticreg_set']['nic1']
        )
        sreg = StaticReg.objects.get(
            pk=blobs['systems'][hostname]['staticreg_set']['nic1']['pk']
        )
        self.assertTrue(sreg)
        self.assertTrue(sreg.system)

        # Change the views and ip address. Make sure the updates worked.
        new_ip = "10.8.75.11"
        blobs['systems'][hostname]['staticreg_set']['nic1']['ip_str'] = new_ip
        blobs['systems'][hostname]['staticreg_set']['nic1']['views'] = [
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
        {{
            "systems": {{
                "{hostname}": {{
                    "asset_tag": "7349",
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
                    "staticreg_set": {{
                        "nic1": {{
                            "description": "Migrated SREG",
                            "views": [{private_view_pk}],
                            "fqdn": "{hostname}",
                            "ttl": null,
                            "ip_type": "4",
                            "ip_str": "10.8.75.10",
                            "hwadapter_set": {{
                                "hw0": {{
                                    "mac": "44:1E:A1:5C:01:B4",
                                    "name": "hw0",
                                    "enable_dhcp": true,
                                    "description": null,
                                    "keyvalue_set": {{
                                        "{hostname}": {{
                                          "key": "hostname",
                                          "value": "{hostname}"
                                        }},
                                        "phx1-vlan80": {{
                                          "key": "dhcp_scope",
                                          "value": "phx1-vlan80"
                                        }}
                                    }}
                                }}
                            }}
                        }}
                    }}
                }}
            }}
        }}
        """.format(
            allocation_pk=self.allocation.pk, hostname=hostname,
            private_view_pk=self.private_view.pk
        )
        blobs, error = bulk_import(data)
        self.assertFalse(error)
        self.assertTrue(
            'pk' in blobs['systems'][hostname]['staticreg_set']['nic1']
        )
        sreg = StaticReg.objects.get(
            pk=blobs['systems'][hostname]['staticreg_set']['nic1']['pk']
        )
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
        {{
            "systems": {{
                "{hostname}": {{
                    "asset_tag": "7349",
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
                    "staticreg_set": {{
                        "nic1": {{
                            "description": "Migrated SREG",
                            "views": [{private_view_pk}],
                            "fqdn": "{hostname}",
                            "ttl": null,
                            "ip_type": "4",
                            "ip_str": "10.8.75.10",
                            "hwadapter_set": {{
                                "hw0": {{
                                    "mac": "44:1E:A1:5C:01:B4",
                                    "name": "hw0",
                                    "enable_dhcp": true,
                                    "description": null,
                                    "keyvalue_set": {{
                                        "{hostname}": {{
                                          "key": "hostname",
                                          "value": "{hostname}"
                                        }},
                                        "phx1-vlan80": {{
                                          "key": "dhcp_scope",
                                          "value": "phx1-vlan80"
                                        }}
                                    }}
                                }}
                            }}
                        }}
                    }}
                }}
            }}
        }}
        """.format(
            allocation_pk=self.allocation.pk, hostname=hostname,
            private_view_pk=View.objects.get(name='private').pk
        )
        blobs, error = bulk_import(data)
        self.assertFalse(error)
        self.assertTrue(
            'pk' in blobs['systems'][hostname]['staticreg_set']['nic1']
        )
        sreg = StaticReg.objects.get(
            pk=blobs['systems'][hostname]['staticreg_set']['nic1']['pk']
        )
        hw = sreg.hwadapter_set.get(mac="44:1E:A1:5C:01:B4")
        kv = hw.keyvalue_set.get(key='hostname')
        self.assertTrue(sreg)
        self.assertTrue(sreg.system)
        self.assertEqual(1, sreg.hwadapter_set.all().count())

        # Change the mac, make things are saved
        new_hostname = 'asdfasdf' + hostname
        new_mac = "44:1E:A1:5C:01:99"
        blobs['systems'][hostname]['staticreg_set']['nic1']['hwadapter_set']['hw0']['mac'] = new_mac  # noqa
        # Chage the hostname in the kv set too
        kvs = blobs['systems'][hostname]['staticreg_set']['nic1']['hwadapter_set']['hw0']['keyvalue_set'].values()  # noqa
        for kv in kvs:
            if kv['key'] == 'hostname':
                kv['value'] = new_hostname

        blobs, error = bulk_import(blobs, load_json=False)

        hw = hw.__class__.objects.get(pk=hw.pk)
        kv = hw.keyvalue_set.get(key='hostname')
        self.assertEqual(new_mac, hw.mac)
        self.assertEqual(new_hostname, kv.value)

    def test_single_cname_create(self):
        hostname = 'puppet99.foobar.mozilla.com'
        data = """
        {{
            "systems": {{
                "{hostname}": {{
                    "asset_tag": "7349",
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
                    "staticreg_set": {{
                        "nic1": {{
                            "cname": [
                                {{
                                    "description": "",
                                    "views": [{private_view_pk}],
                                    "fqdn": "puppet99.build.mozilla.org",
                                    "target": "{hostname}",
                                    "ttl": null
                                }}
                            ],
                            "description": "Migrated SREG",
                            "views": [{private_view_pk}],
                            "fqdn": "{hostname}",
                            "ttl": null,
                            "ip_type": "4",
                            "ip_str": "10.8.75.10",
                            "hwadapter_set": {{
                                "hw0": {{
                                    "mac": "44:1E:A1:5C:01:B4",
                                    "name": "hw0",
                                    "enable_dhcp": true,
                                    "description": null,
                                    "keyvalue_set": {{
                                        "{hostname}": {{
                                          "key": "hostname",
                                          "value": "{hostname}"
                                        }},
                                        "phx1-vlan80": {{
                                          "key": "dhcp_scope",
                                          "value": "phx1-vlan80"
                                        }}
                                    }}
                                }}
                            }}
                        }}
                    }}
                }}
            }}
        }}
        """.format(
            allocation_pk=self.allocation.pk, hostname=hostname,
            private_view_pk=self.private_view.pk
        )
        blobs, error = bulk_import(data)
        self.assertFalse(error)
        self.assertTrue(
            'pk' in blobs['systems'][hostname]['staticreg_set']['nic1']
        )
        self.assertEqual(
            1, len(blobs['systems'][hostname]['staticreg_set']['nic1']['cname'])  # noqa
        )
        self.assertTrue(
            'pk' in blobs['systems'][hostname]['staticreg_set']['nic1']['cname'][0]  # noqa
        )
        sreg = StaticReg.objects.get(
            pk=blobs['systems'][hostname]['staticreg_set']['nic1']['pk']
        )
        self.assertTrue(sreg)
        cname = CNAME.objects.get(
            pk=blobs['systems'][hostname]['staticreg_set']['nic1']['cname'][0]['pk']  # noqa
        )
        self.assertTrue(cname.views.filter(name='private').exists())

    def test_single_cname_update(self):
        hostname = 'puppet101.foobar.mozilla.com'
        data = """
        {{
            "systems": {{
                "{hostname}": {{
                    "asset_tag": "7349",
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
                    "staticreg_set": {{
                        "nic1": {{
                            "cname": [
                                {{
                                    "description": "",
                                    "views": [{private_view_pk}],
                                    "fqdn": "puppet99.build.mozilla.org",
                                    "target": "{hostname}",
                                    "ttl": null
                                }}
                            ],
                            "description": "Migrated SREG",
                            "views": [{private_view_pk}],
                            "fqdn": "{hostname}",
                            "ttl": null,
                            "ip_type": "4",
                            "ip_str": "10.8.75.10",
                            "hwadapter_set": {{
                                "hw0": {{
                                    "mac": "44:1E:A1:5C:01:B4",
                                    "name": "hw0",
                                    "enable_dhcp": true,
                                    "description": null,
                                    "keyvalue_set": {{
                                        "{hostname}": {{
                                          "key": "hostname",
                                          "value": "{hostname}"
                                        }},
                                        "phx1-vlan80": {{
                                          "key": "dhcp_scope",
                                          "value": "phx1-vlan80"
                                        }}
                                    }}
                                }}
                            }}
                        }}
                    }}
                }}
            }}
        }}
        """.format(
            allocation_pk=self.allocation.pk, hostname=hostname,
            private_view_pk=self.private_view.pk
        )
        blobs, error = bulk_import(data)
        self.assertFalse(error)
        self.assertTrue(
            'pk' in blobs['systems'][hostname]['staticreg_set']['nic1']
        )
        self.assertEqual(
            1, len(blobs['systems'][hostname]['staticreg_set']['nic1']['cname'])  # noqa
        )
        self.assertTrue(
            'pk' in blobs['systems'][hostname]['staticreg_set']['nic1']['cname'][0]  # noqa
        )
        sreg = StaticReg.objects.get(
            pk=blobs['systems'][hostname]['staticreg_set']['nic1']['pk']
        )
        self.assertTrue(sreg)
        cname = CNAME.objects.get(
            pk=blobs['systems'][hostname]['staticreg_set']['nic1']['cname'][0]['pk']  # noqa
        )
        self.assertTrue(cname.views.filter(name='private').exists())

        new_fqdn = 'asdfasdfasdf.build.mozilla.org'
        blobs['systems'][hostname]['staticreg_set']['nic1']['cname'][0]['fqdn'] = new_fqdn  # noqa

        blobs, error = bulk_import(blobs, load_json=False)
        cname = CNAME.objects.get(pk=cname.pk)
        self.assertEqual(new_fqdn, cname.fqdn)
