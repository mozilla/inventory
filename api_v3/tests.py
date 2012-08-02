from system_api import SystemResource, CustomAPIResource, OperatingSystemData
from systems.models import System
from tastypie.test import ResourceTestCase
from django.core.exceptions import ValidationError
import json
from django.http import HttpRequest


class Tasty1SystemTest(ResourceTestCase):

    test_hostname = 'foobar.vlan.dc'

    def setUp(self):
        super(Tasty1SystemTest, self).setUp()

    def create_system(self, host_dict):
        System(**host_dict).save()

    def test1_system_not_exist(self):
        resp = self.api_client.get('/api/v3/system/1/', format='json')
        self.assertEqual(resp.status_code, 404)

    def test2_create_system(self):
        data = {'hostname': self.test_hostname}
        resp = self.api_client.post(
            '/en-US/tasty/v3/system/', format='json', data=data)
        self.assertEqual(resp.status_code, 201)

    def test3_get_system_by_id(self):
        self.create_system({'hostname': self.test_hostname})
        resp = self.api_client.get('/en-US/tasty/v3/system/2/', format='json')
        self.assertEqual(resp.status_code, 200)

    def test4_get_system_by_hostname(self):
        self.create_system({'hostname': self.test_hostname})
        resp = self.api_client.get(
            '/en-US/tasty/v3/system/%s/' % self.test_hostname, format='json')
        self.assertEqual(resp.status_code, 200)

    def test5_delete_system_by_id(self):
        self.create_system({'hostname': self.test_hostname})
        self.assertEqual(len(System.objects.all()), 1)
        resp = self.api_client.get(
            '/en-US/tasty/v3/system/%s/' % self.test_hostname, format='json')
        system_id = self.deserialize(resp)['id']
        resp = self.api_client.delete(
            '/en-US/tasty/v3/system/%i/' % system_id, format='json')
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(len(System.objects.all()), 0)

    def test6_delete_system_by_hostname(self):
        self.create_system({'hostname': self.test_hostname})
        self.assertEqual(len(System.objects.all()), 1)
        resp = self.api_client.delete(
            '/en-US/tasty/v3/system/%s/' % self.test_hostname, format='json')
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(len(System.objects.all()), 0)

    def test8_overridden_system_schema(self):
        request = HttpRequest()
        request.method = 'GET'
        sr = SystemResource()
        the_ret = sr.get_schema(request)
        obj = json.loads(the_ret.content)
        self.assertTrue('auto_create_interface' in obj['fields'])
        self.assertTrue('delete_interface' in obj['fields'])
        self.assertTrue('update_interface' in obj['fields'])
        self.assertTrue('mac_address' in obj['fields'])
        self.assertTrue('ip_address' in obj['fields'])
        self.assertTrue('interface' in obj['fields'])

    def test9_test_default_format(self):
        request = HttpRequest()
        request.method = 'GET'
        cr = CustomAPIResource()
        the_ret = cr.get_schema(request)
        self.assertEqual(the_ret._headers['content-type'][1],
            'application/json; charset=utf-8')

    def test10_test_format(self):
        request = HttpRequest()
        request.method = 'GET'
        request.GET['format'] = 'json'
        cr = CustomAPIResource()
        the_ret = cr.get_schema(request)
        self.assertEqual(the_ret._headers['content-type'][1],
            'application/json; charset=utf-8')


class Tasty2SystemNetworkAdapterTest(ResourceTestCase):

    test_hostname = 'foobar.vlan.dc'

    def setUp(self):
        super(Tasty2SystemNetworkAdapterTest, self).setUp()

    def create_system(self, host_dict):
        System(**host_dict).save()

    def create_domains(self):
        from mozdns.domain.models import Domain
        from core.network.models import Network
        from core.range.models import Range
        Domain(name='com').save()
        Domain(name='mozilla.com').save()
        Domain(name='dc.mozilla.com').save()
        Domain(name='vlan.dc.mozilla.com').save()
        Domain(name='arpa').save()
        Domain(name='in-addr.arpa').save()
        Domain(name='10.in-addr.arpa').save()
        network = Network(network_str="10.0.0.0/8", ip_type='4')
        network.update_network()
        network.save()
        r = Range(
            start_str='10.99.99.0', end_str='10.99.99.254', network=network)
        r.clean()
        r.save()

    def test1_create_system_with_auto_assigned_magic(self):
        self.create_domains()
        data = {
            'hostname': self.test_hostname,
            'auto_create_interface': 'True',
            'mac_address': '00:00:00:00:00:00', }
        resp = self.api_client.post(
            '/en-US/tasty/v3/system/', format='json', data=data)
        self.assertEqual(resp.status_code, 201)
        resp = self.api_client.get(
            '/en-US/tasty/v3/system/%s/' % self.test_hostname, format='json')
        system_tmp = self.deserialize(resp)
        system = System.objects.get(id=system_tmp['id'])
        eth0 = system.staticinterface_set.all()[0]
        eth0.update_attrs()
        self.assertEqual(eth0.ip_str, '10.99.99.97')
        self.assertEqual(eth0.mac, '00:00:00:00:00:00')
        self.assertEqual(eth0.ip_type, '4')
        self.assertEqual(eth0.attrs.primary, '0')
        self.assertEqual(eth0.attrs.interface_type, 'eth')
        self.assertEqual(eth0.attrs.alias, '0')

    def test2_create_system_with_static_ip(self):
        self.create_domains()
        data = {
            'hostname': self.test_hostname,
            'auto_create_interface': 'True',
            'mac_address': '00:00:00:00:00:00',
            'ip_address': '10.99.99.99', }
        resp = self.api_client.post(
            '/en-US/tasty/v3/system/', format='json', data=data)
        self.assertEqual(resp.status_code, 201)
        resp = self.api_client.get(
            '/en-US/tasty/v3/system/%s/' % self.test_hostname, format='json')
        system_tmp = self.deserialize(resp)
        system = System.objects.get(id=system_tmp['id'])
        eth0 = system.staticinterface_set.all()[0]
        self.assertEqual(eth0.ip_str, '10.99.99.99')
        self.assertEqual(eth0.mac, '00:00:00:00:00:00')
        self.assertEqual(eth0.ip_type, '4')

    def test3_extract_nic_attrs(self):
        nic_name = "eth0.0"
        name, primary, alias = SystemResource.extract_nic_attrs(nic_name)
        self.assertEqual(name, "eth")
        self.assertEqual(primary, "0")
        self.assertEqual(alias, "0")

        nic_name = "eth1.0"
        name, primary, alias = SystemResource.extract_nic_attrs(nic_name)
        self.assertEqual(name, "eth")
        self.assertEqual(primary, "1")
        self.assertEqual(alias, "0")

        nic_name = "eth42.19"
        name, primary, alias = SystemResource.extract_nic_attrs(nic_name)
        self.assertEqual(name, "eth")
        self.assertEqual(primary, "42")
        self.assertEqual(alias, "19")

    def test4_extract_nic_attrs_bad_interface(self):
        nic_name = "eth17"
        self.assertRaises(
            ValidationError, SystemResource.extract_nic_attrs, nic_name)

    def test5_create_system_with_assigned_interface_and_ip(self):
        self.create_domains()
        data = {
            'hostname': self.test_hostname,
            'auto_create_interface': 'True',
            'mac_address': '00:00:00:00:00:00',
            'interface': 'mgmt2.5',
            'ip_address': '10.99.99.99', }
        resp = self.api_client.post(
            '/en-US/tasty/v3/system/', format='json', data=data)
        self.assertEqual(resp.status_code, 201)
        resp = self.api_client.get(
            '/en-US/tasty/v3/system/%s/' % self.test_hostname, format='json')
        system_tmp = self.deserialize(resp)
        system = System.objects.get(id=system_tmp['id'])
        eth0 = system.staticinterface_set.all()[0]
        eth0.update_attrs()
        self.assertEqual(eth0.ip_str, '10.99.99.99')
        self.assertEqual(eth0.mac, '00:00:00:00:00:00')
        self.assertEqual(eth0.ip_type, '4')
        self.assertEqual(eth0.attrs.primary, '2')
        self.assertEqual(eth0.attrs.interface_type, 'mgmt')
        self.assertEqual(eth0.attrs.alias, '5')

    def test6_system_model_next_available_network_adapter_no_adapters(self):
        self.create_domains()
        data = {
            'hostname': self.test_hostname, }
        self.api_client.post(
            '/en-US/tasty/v3/system/', format='json', data=data)
        resp = self.api_client.get(
            '/en-US/tasty/v3/system/%s/' % self.test_hostname, format='json')
        system_tmp = self.deserialize(resp)
        system = System.objects.get(id=system_tmp['id'])
        name, primary, alias = system.get_next_adapter()
        self.assertEqual(name, 'eth')
        self.assertEqual(primary, '0')
        self.assertEqual(alias, '0')

    def test7_test_system_model_next_available_network_adapter(self):
        self.create_domains()
        data = {
            'hostname': self.test_hostname,
            'auto_create_interface': 'True',
            'mac_address': '00:00:00:00:00:00',
            'ip_address': '10.99.99.99', }
        resp = self.api_client.post(
            '/en-US/tasty/v3/system/', format='json', data=data)
        resp = self.api_client.get(
            '/en-US/tasty/v3/system/%s/' % self.test_hostname, format='json')
        system_tmp = self.deserialize(resp)
        system = System.objects.get(id=system_tmp['id'])
        name, primary, alias = system.get_next_adapter()
        self.assertEqual(name, 'eth')
        self.assertEqual(primary, '1')
        self.assertEqual(alias, '0')

    def test8_test_system_model_delete_by_adapter_via_orm(self):
        self.create_domains()
        data = {
            'hostname': self.test_hostname,
            'auto_create_interface': 'True',
            'mac_address': '00:00:00:00:00:00',
            'ip_address': '10.99.99.99', }
        resp = self.api_client.post(
            '/en-US/tasty/v3/system/', format='json', data=data)
        resp = self.api_client.get(
            '/en-US/tasty/v3/system/%s/' % self.test_hostname, format='json')
        system_tmp = self.deserialize(resp)
        system = System.objects.get(id=system_tmp['id'])
        adapters = system.get_adapters()
        self.assertEqual(len(adapters), 1)
        self.assertEqual(adapters[0].attrs.interface_type, 'eth')
        self.assertEqual(adapters[0].attrs.primary, '0')
        self.assertEqual(adapters[0].attrs.alias, '0')
        system.delete_adapter('eth0.0')
        adapters = system.get_adapters()
        self.assertEqual(adapters, None)

    def test9_test_system_model_delete_by_adapter_via_api(self):
        self.create_domains()
        data = {
            'hostname': self.test_hostname,
            'auto_create_interface': 'True',
            'mac_address': '00:00:00:00:00:00',
            'ip_address': '10.99.99.99', }
        delete_data = {
            'delete_interface': 'True',
            'interface': 'eth0.0', }
        resp = self.api_client.post(
            '/en-US/tasty/v3/system/', format='json', data=data)
        resp = self.api_client.get(
            '/en-US/tasty/v3/system/%s/' % self.test_hostname, format='json')
        system_tmp = self.deserialize(resp)
        system = System.objects.get(id=system_tmp['id'])
        adapters = system.get_adapters()
        self.assertEqual(len(adapters), 1)
        self.assertEqual(adapters[0].attrs.interface_type, 'eth')
        self.assertEqual(adapters[0].attrs.primary, '0')
        self.assertEqual(adapters[0].attrs.alias, '0')
        resp = self.api_client.put(
            '/en-US/tasty/v3/system/%s/' % self.test_hostname,
            format='json', data=delete_data)
        resp = self.api_client.get(
            '/en-US/tasty/v3/system/%s/' % self.test_hostname, format='json')
        system_tmp = self.deserialize(resp)
        system = System.objects.get(id=system_tmp['id'])
        adapters = system.get_adapters()
        self.assertEqual(adapters, None)

    def test10_test_system_model_update_adapter_via_orm(self):
        self.create_domains()
        data = {
            'hostname': self.test_hostname,
            'auto_create_interface': 'True',
            'mac_address': '00:00:00:00:00:00',
            'ip_address': '10.99.99.99', }
        resp = self.api_client.post(
            '/en-US/tasty/v3/system/', format='json', data=data)
        resp = self.api_client.get(
            '/en-US/tasty/v3/system/%s/' % self.test_hostname, format='json')
        system_tmp = self.deserialize(resp)
        system = System.objects.get(id=system_tmp['id'])
        adapters = system.get_adapters()
        self.assertEqual(len(adapters), 1)
        self.assertEqual(adapters[0].attrs.interface_type, 'eth')
        self.assertEqual(adapters[0].attrs.primary, '0')
        self.assertEqual(adapters[0].attrs.alias, '0')
        self.assertEqual(adapters[0].ip_str, '10.99.99.99')
        self.assertEqual(adapters[0].mac, '00:00:00:00:00:00')
        update_dict = {
            "ip_address": "10.99.99.1",
            "interface": "eth0.0",
            "mac_address": "AA:AA:AA:AA:AA:AA", }
        system.update_adapter(**update_dict)
        adapters = system.get_adapters()
        self.assertEqual(len(adapters), 1)
        self.assertEqual(adapters[0].attrs.interface_type, 'eth')
        self.assertEqual(adapters[0].attrs.primary, '0')
        self.assertEqual(adapters[0].attrs.alias, '0')
        self.assertEqual(adapters[0].ip_str, '10.99.99.1')
        self.assertEqual(adapters[0].mac, 'AA:AA:AA:AA:AA:AA')

    def test11_test_system_model_delete_by_adapter_via_api(self):
        self.create_domains()
        data = {
            'hostname': self.test_hostname,
            'auto_create_interface': 'True',
            'mac_address': '00:00:00:00:00:00',
            'ip_address': '10.99.99.99', }
        update_dict = {
            "ip_address": "10.99.99.1",
            "interface": "eth0.0",
            "update_interface": "true",
            "mac_address": "AA:AA:AA:AA:AA:AA", }
        resp = self.api_client.post(
            '/en-US/tasty/v3/system/', format='json', data=data)
        resp = self.api_client.get(
            '/en-US/tasty/v3/system/%s/' % self.test_hostname, format='json')
        system_tmp = self.deserialize(resp)
        system = System.objects.get(id=system_tmp['id'])
        adapters = system.get_adapters()
        self.assertEqual(len(adapters), 1)
        self.assertEqual(adapters[0].attrs.interface_type, 'eth')
        self.assertEqual(adapters[0].attrs.primary, '0')
        self.assertEqual(adapters[0].attrs.alias, '0')
        self.assertEqual(adapters[0].ip_str, '10.99.99.99')
        self.assertEqual(adapters[0].mac, '00:00:00:00:00:00')
        resp = self.api_client.put(
            '/en-US/tasty/v3/system/%s/' % self.test_hostname,
            format='json', data=update_dict)
        resp = self.api_client.get(
            '/en-US/tasty/v3/system/%s/' %
            self.test_hostname, format='json')
        system_tmp = self.deserialize(resp)
        system = System.objects.get(id=system_tmp['id'])
        adapters = system.get_adapters()
        self.assertEqual(len(adapters), 1)
        self.assertEqual(adapters[0].attrs.interface_type, 'eth')
        self.assertEqual(adapters[0].attrs.primary, '0')
        self.assertEqual(adapters[0].attrs.alias, '0')
        self.assertEqual(adapters[0].ip_str, '10.99.99.1')
        self.assertEqual(adapters[0].mac, 'AA:AA:AA:AA:AA:AA')
