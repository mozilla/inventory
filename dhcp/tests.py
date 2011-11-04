from django.test import TestCase
from django.test.client import Client
import json
class TruthTest(TestCase):
    fixtures = ['testdata.json']

    def setUp(self):
        self.client = Client()

    def test_get_dhcp_scope_by_name(self):
        resp = self.client.get('/api/keyvalue/?keystore=phx-vlan73')
        obj = json.loads(resp.content)
        self.assertEqual(obj['dhcp.scope.start'],'10.0.1.0')
        self.assertEqual(obj['dhcp.scope.end'],'10.0.1.255')

    def test_output_dhcp_config(self):
        resp = self.client.get('/dhcp/showfile/1')
        #print resp
        #print resp.status_code
        #print resp.content
    def test_get_dhcp_scopes_by_api(self):
        resp = self.client.get('/api/keyvalue/?key=is_dhcp_scope')
        obj = json.loads(resp.content)
        self.assertEqual(2,len(obj))
        self.assertEqual(obj['truth:phx-vlan73:is_dhcp_scope'], 'True')
        self.assertEqual(obj['truth:test:is_dhcp_scope'], 'False')

    def test_get_dhcp_key_value(self):
        dhcp_scope = 'phx-vlan73'
        resp = self.client.get('/api/keyvalue/?keystore=%s' % dhcp_scope)
        obj = json.loads(resp.content)
        #self.assertEqual(2,len(obj))
        #self.assertEqual(obj['truth:phx-vlan73:is_dhcp_scope'], 'True')
        #self.assertEqual(obj['truth:test:is_dhcp_scope'], 'True')

    def test_dhcp_scope_names_and_descriptions(self):
        dhcp_scope = 'phx-vlan73'
        resp = self.client.get('/api/v2/dhcp/%s/get_scopes_with_names/' % dhcp_scope)
        obj = json.loads(resp.content)
        self.assertEqual(obj[0]['name'], 'phx-vlan73')
        self.assertEqual(obj[0]['description'], 'PHX Vlan 73 DHCP Scope')

    def test_update_dhcp_scope_value(self):
        dhcp_scope = 'phx-vlan73'
        resp = self.client.put('/api/keyvalue/%s/' % dhcp_scope, {'key':'dhcp.scope.start', 'value':'1.1.1.1'})
        resp = self.client.put('/api/keyvalue/%s/' % dhcp_scope, {'key':'dhcp.scope.start2', 'value':'9.9.9.9'})
        if resp.status_code == 404:
            #print 'does not exist'
            resp = self.client.post('/api/keyvalue/%s/' % dhcp_scope, {'key':'dhcp.scope.start2', 'value':'9.9.9.9', 'truth_name':dhcp_scope})
            #print resp.content
        resp = self.client.get('/api/keyvalue/?keystore=%s' % dhcp_scope)
        obj = json.loads(resp.content)
        #print obj




