from django.test import TestCase
from django.test.client import Client
try:
    import json
except:
    from django.utils import simplejson as json
from MacroExpansion import MacroExpansion
from KeyValueTree import KeyValueTree
from truth.models import Truth, KeyValue as TruthKeyValue


class TestMacroExpansion(TestCase):
    fixtures = ['testdata.json']
    def test_import(self):
        try:
            from MacroExpansion import MacroExpansion
        except:
            raise(BaseException('Unable to import Macro Expansion'))
        try:
            from KeyValueTree import KeyValueTree
        except:
            raise(BaseException('Unable to import KeyValueTree'))
    def test_key_value_not_found(self):
        m = MacroExpansion('host:fake-hostname2:ip_address')
        self.assertEqual(m.output(),'10.99.32.1')
    def test_key_value_found(self):
        m = MacroExpansion('host:fake-hostname2:ip_address')
        self.assertEqual(m.output(),'10.99.32.1')

#TODO Add checks for setting every property of a sytem through the api
class SystemApi(TestCase):
    fixtures = ['testdata.json']
    new_hostname = 'new_hostname999'
    new_host_id = 5

    def setup(self):
        self.client = Client()

    def test_get_system_not_found_by_id(self):
        resp = self.client.get('/api/system/-1/', follow=True)
        self.assertEqual(404, resp.status_code)

    def test_get_system_by_id(self):
        resp = self.client.get('/api/system/1/', follow=True)
        self.assertEqual(200, resp.status_code)

    def test_get_system_by_hostname(self):
        resp = self.client.get('/api/system/asfdasfasfasdfasfasdfsadf/', follow=True)
        self.assertEqual(404, resp.status_code)
        resp = self.client.get('/api/system/fake-hostname2/', follow=True)
        self.assertEqual(200, resp.status_code)

    def test_create_system(self):
        resp = self.client.post('/api/system/%s/' % self.new_hostname, follow=True)
        self.assertEqual(201, resp.status_code)
        resp = self.client.get('/api/system/%i/' % 3, follow=True)
        self.assertEqual(200, resp.status_code)
        resp = self.client.get('/api/system/%s/' % self.new_hostname, follow=True)
        self.assertEqual(200, resp.status_code)
        self.assertEqual(json.loads(resp.content)['hostname'], self.new_hostname)

    def test_update_system(self):
        resp = self.client.post('/api/system/%s/' % self.new_hostname, follow=True)
        self.assertEqual(201, resp.status_code)
        resp = self.client.put('/api/system/%i/' % (self.new_host_id), {'hostname':'updated_hostname'}, follow=True)
        self.assertEqual(200, resp.status_code)
        resp = self.client.get('/api/system/%i/' % (self.new_host_id), follow=True)
        self.assertEqual(200, resp.status_code)
        self.assertEqual(json.loads(resp.content)['hostname'], 'updated_hostname')

    def test_delete_system(self):
        resp = self.client.post('/api/system/%s/' % self.new_hostname, follow=True)
        self.assertEqual(201, resp.status_code)
        resp = self.client.delete('/api/system/%i/' % (4), follow=True)
        self.assertEqual(200, resp.status_code)
        resp = self.client.get('/api/system/%i/' % (self.new_host_id), follow=True)
        self.assertEqual(404, resp.status_code)
        resp = self.client.get('/api/system/%s/' % self.new_hostname, follow=True)
        self.assertEqual(404, resp.status_code)
    def test_key_value_tree(self):
        tree = KeyValueTree('fake-hostname2').final
        self.assertEqual(tree['nic.0.ipv4_address.0'],'10.99.32.1')

    def test_key_value_api(self):
        resp = self.client.get('/api/keyvalue/?keystore=fake-hostname2', follow=True)
        print resp.content
        self.assertEqual(json.loads(resp.content)['truth:test:cluster_name'], 'Test Cluster Name')
        self.assertEqual(json.loads(resp.content)['host:fake-hostname1:nic.0.ipv4_address.0'], u'10.99.32.3')

        resp = self.client.get('/api/keyvalue/?key=ip_address', follow=True)
        self.assertEqual(json.loads(resp.content)['host:fake-hostname1:ip_address'], '10.99.32.3')

        resp = self.client.get('/api/keyvalue/?key=cluster_owner', follow=True)
        self.assertEqual(json.loads(resp.content)['truth:test:cluster_owner'], 'The Cluster Owner')

        resp = self.client.get('/api/keyvalue/?value=10.99.32.3', follow=True)
        self.assertEqual(json.loads(resp.content)['host:fake-hostname1:ip_address'], '10.99.32.3')
class DHCPApi(TestCase):
    fixtures = ['testdata.json']

    def setup(self):
        self.client = Client()

    def test_get_single_scope(self):
        resp = self.client.get('/api/keyvalue/?key_type=dhcp_scopes', follow=True)
        scope_list = json.loads(resp.content)
        self.assertEqual(scope_list[0]['dhcp.is_scope'], 'True')
        self.assertEqual(scope_list[0]['dhcp.scope.start'], '10.0.1.0')
        self.assertEqual(scope_list[0]['dhcp.scope.end'], '10.0.1.255')
        self.assertEqual(scope_list[0]['dhcp.scope.name'], 'phx-vlan73')

    def test_get_second_scope(self):
        resp = self.client.get('/api/keyvalue/?key_type=dhcp_scopes', follow=True)
        scope_list = json.loads(resp.content)
        """self.assertEqual(scope_list[1]['dhcp.is_scope'], 'True')
        self.assertEqual(scope_list[1]['dhcp.scope.start'], '10.0.0.0')
        self.assertEqual(scope_list[1]['dhcp.scope.end'], '10.0.0.255')
        self.assertEqual(scope_list[1]['dhcp.scope.name'], 'phx-vlan81')"""

    def test_get_multiple_scopes(self):
        resp = self.client.get('/api/keyvalue/?key_type=dhcp_scopes', follow=True)
        scope_list = json.loads(resp.content)
        """self.assertEqual(scope_list[0]['dhcp.is_scope'], 'True')
        self.assertEqual(scope_list[0]['dhcp.scope.start'], '10.0.1.0')
        self.assertEqual(scope_list[0]['dhcp.scope.end'], '10.0.1.255')
        self.assertEqual(scope_list[0]['dhcp.scope.name'], 'phx-vlan73')
        self.assertEqual(scope_list[1]['dhcp.is_scope'], 'True')
        self.assertEqual(scope_list[1]['dhcp.scope.start'], '10.0.0.0')
        self.assertEqual(scope_list[1]['dhcp.scope.end'], '10.0.0.255')
        self.assertEqual(scope_list[1]['dhcp.scope.name'], 'phx-vlan81')"""

    def test_get_system_by_scope(self):
        resp = self.client.get('/api/keyvalue/?key_type=system_by_scope&scope=phx-vlan73', follow=True)
        system_list = json.loads(resp.content)
        self.assertEqual(system_list[0]['nic.0.mac_address.0'],'00:00:00:00:00:AA')
        self.assertEqual(system_list[0]['nic.0.ipv4_address.0'],'10.99.32.1')
        self.assertEqual(system_list[0]['nic.1.mac_address.0'],'00:00:00:00:00:BB')
        self.assertEqual(system_list[0]['nic.1.ipv4_address.0'],'10.99.32.2')

    def test_get_adapters_by_system(self):
        resp = self.client.get('/api/keyvalue/?key_type=adapters_by_system&system=fake-hostname2', follow=True)
        system_list = json.loads(resp.content)
        #print system_list
    def test_delete_network_adapter(self):
        resp = self.client.delete('/api/keyvalue/1/', {'system_hostname':'fake-hostname2', 'adapter_number':'0', 'key_type':'delete_network_adapter'}, follow=True)
        #print "The content is %s" % resp.content
