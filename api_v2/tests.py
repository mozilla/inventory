from django.test import TestCase
from django.core.urlresolvers import reverse
from django.test.client import Client
try:
    import json
except:
    from django.utils import simplejson as json
from MacroExpansion import MacroExpansion
from KeyValueTree import KeyValueTree
from truth.models import Truth, KeyValue as TruthKeyValue
from systems.models import ScheduledTask, System, KeyValue


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

## Test that the oncall api is returning the proper people from our test fixture
class TestOnCall(TestCase):
    fixtures = ['user_systems_test_data.json']
    FORCE_DB = True
    def setup(self):
        self.client = Client()

    def test_get_current_desktop_oncall_email(self):
        resp = self.client.get('/api/v2/oncall/desktop/email/', follow=True)
        self.assertEqual(200, resp.status_code)
        obj = json.loads(resp.content)
        self.assertEqual(obj['user'], 'user1@domain.com')
        self.assertEqual(obj['epager_address'], 'user1@domain.com')

        resp = self.client.put('/en-US/api/v2/oncall/setsysadmin/user1@domain.com/', follow=True)
        self.assertEqual(200, resp.status_code)
        resp = self.client.get('/api/v2/oncall/desktop/email/', follow=True)
        self.assertEqual(200, resp.status_code)

        obj = json.loads(resp.content)
        self.assertEqual(obj['user'], 'user1@domain.com')

    def test_get_current_desktop_oncall_irc_nick(self):
        resp = self.client.get('/api/v2/oncall/sysadmin/irc_nick/', follow=True)
        self.assertEqual(200, resp.status_code)
        obj = json.loads(resp.content)
        self.assertEqual(obj['user'], 'user2')

    def test_get_current_sysadmin_oncall(self):
        resp = self.client.get('/api/v2/oncall/sysadmin/email/', follow=True)
        self.assertEqual(200, resp.status_code)
        obj = json.loads(resp.content)
        self.assertEqual(obj['user'], 'user2@domain.com')

    def test_get_all_sysadmin_oncall(self):
        resp = self.client.get('/api/v2/oncall/sysadmin/all/', follow=True)
        self.assertEqual(200, resp.status_code)
        obj = json.loads(resp.content)
        self.assertEqual(len(obj), 3)
        self.assertEqual('user3', obj[2]['user'])

    def test_get_all_desktop_oncall(self):
        resp = self.client.get('/api/v2/oncall/desktop/all/', follow=True)
        self.assertEqual(200, resp.status_code)
        obj = json.loads(resp.content)
        self.assertEqual(len(obj), 3)
        self.assertEqual('user4', obj[2]['user'])

    def test_set_desktop_oncall(self):
        resp = self.client.get('/api/v2/oncall/desktop/email/', follow=True)
        self.assertEqual(200, resp.status_code)
        obj = json.loads(resp.content)
        self.assertEqual('user1@domain.com', obj['user'])

        resp = self.client.put('/en-US/api/v2/oncall/setdesktop/user3@domain.com/', follow=True)
        self.assertEqual(200, resp.status_code)

        resp = self.client.get('/api/v2/oncall/desktop/email/', follow=True)
        self.assertEqual(200, resp.status_code)
        obj = json.loads(resp.content)
        self.assertEqual('user3@domain.com', obj['user'])

    def test_set_desktop_oncall_by_irc_nick(self):
        resp = self.client.get('/api/v2/oncall/desktop/email/', follow=True)
        self.assertEqual(200, resp.status_code)
        obj = json.loads(resp.content)
        self.assertEqual('user1@domain.com', obj['user'])

        resp = self.client.put('/en-US/api/v2/oncall/setdesktop/user3/', follow=True)
        self.assertEqual(200, resp.status_code)

        resp = self.client.get('/api/v2/oncall/desktop/email/', follow=True)
        self.assertEqual(200, resp.status_code)
        obj = json.loads(resp.content)
        self.assertEqual('user3@domain.com', obj['user'])

    def test_set_sysadmin_oncall(self):

        resp = self.client.get('/api/v2/oncall/sysadmin/email/', follow=True)
        self.assertEqual(200, resp.status_code)
        obj = json.loads(resp.content)
        self.assertEqual('user2@domain.com', obj['user'])

        resp = self.client.put('/en-US/api/v2/oncall/setsysadmin/user3@domain.com/', follow=True)
        self.assertEqual(200, resp.status_code)

        resp = self.client.get('/api/v2/oncall/sysadmin/email/', follow=True)
        self.assertEqual(200, resp.status_code)
        obj = json.loads(resp.content)
        self.assertEqual('user3@domain.com', obj['user'])

    def test_set_sysadmin_oncall_by_irc_nick(self):

        resp = self.client.get('/api/v2/oncall/sysadmin/email/', follow=True)
        self.assertEqual(200, resp.status_code)
        obj = json.loads(resp.content)
        self.assertEqual('user2@domain.com', obj['user'])

        resp = self.client.put('/en-US/api/v2/oncall/setsysadmin/user3/', follow=True)
        self.assertEqual(200, resp.status_code)

        resp = self.client.get('/api/v2/oncall/sysadmin/email/', follow=True)
        self.assertEqual(200, resp.status_code)
        obj = json.loads(resp.content)
        self.assertEqual('user3@domain.com', obj['user'])
#TODO Add checks for setting every property of a sytem through the api
class SystemApi(TestCase):
    fixtures = ['testdata.json']
    new_hostname = 'new_hostname999asdf'

    def setup(self):
        self.client = Client()

    def test_get_system_not_found_by_id(self):
        resp = self.client.get('/api/v2/system/-1/', follow=True)
        self.assertEqual(404, resp.status_code)

    def test_get_system_by_id(self):
        resp = self.client.get('/api/v2/system/1/', follow=True)
        self.assertEqual(200, resp.status_code)

    def test_get_system_by_hostname(self):
        resp = self.client.get('/api/v2/system/asfdasfasfasdfasfasdfsadf/', follow=True)
        self.assertEqual(404, resp.status_code)
        resp = self.client.get('/api/v2/system/fake-hostname2/', follow=True)
        self.assertEqual(200, resp.status_code)

    def test_create_system(self):
        resp = self.client.post('/en-US/api/v2/system/%s/' % self.new_hostname, follow=True)
        self.assertEqual(201, resp.status_code)
        obj = json.loads(resp.content.split(" = ")[1])
        resp = self.client.get('/api/v2/system/%i/' % obj['id'], follow=True)
        self.assertEqual(200, resp.status_code)
        resp = self.client.get('/api/v2/system/%s/' % self.new_hostname, follow=True)
        self.assertEqual(200, resp.status_code)
        self.assertEqual(json.loads(resp.content)['hostname'], self.new_hostname)

    def test_update_system(self):
        self.client.delete('/en-US/api/v2/system/%s/' % self.new_hostname, follow=True)
        resp = self.client.post('/en-US/api/v2/system/%s/' % self.new_hostname, follow=True)
        obj = json.loads(resp.content.split(" = ")[1])
        self.assertEqual(201, resp.status_code)
        resp = self.client.put('/en-US/api/v2/system/%i/' % (obj['id']), {'hostname':'updated_hostname'}, follow=True)
        self.assertEqual(200, resp.status_code)
        resp = self.client.get('/api/v2/system/%i/' % (obj['id']), follow=True)
        self.assertEqual(200, resp.status_code)
        self.assertEqual(json.loads(resp.content)['hostname'], 'updated_hostname')

    def test_delete_system(self):
        resp = self.client.post('/en-US/api/v2/system/%s/' % self.new_hostname, follow=True)
        self.assertEqual(201, resp.status_code)
        obj = json.loads(resp.content.split(" = ")[1])
        resp = self.client.delete('/en-US/api/v2/system/%i/' % (obj['id']), follow=True)
        self.assertEqual(200, resp.status_code)
        obj = json.loads(resp.content.split(" = ")[1])
        resp = self.client.get('/api/v2/system/%i/' % (obj['id']), follow=True)
        self.assertEqual(404, resp.status_code)
        resp = self.client.get('/api/v2/system/%s/' % self.new_hostname, follow=True)
        self.assertEqual(404, resp.status_code)

    def test_key_value_tree(self):
        tree = KeyValueTree('fake-hostname2').final
        self.assertEqual(tree['nic.0.ipv4_address.0'],'10.99.32.1')

    def test_key_value_api(self):
        resp = self.client.get('/api/v2/keyvalue/?keystore=fake-hostname2', follow=True)
        self.assertEqual(json.loads(resp.content)['truth:test:cluster_name'], 'Test Cluster Name')
        self.assertEqual(json.loads(resp.content)['host:fake-hostname1:nic.0.ipv4_address.0'], '10.99.32.3')

        resp = self.client.put('/api/v2/keyvalue/5/', {'key':'nic.0.ipv4_address.0', 'value':'14.14.14.14', 'system_id':'1'}, follow=True)

        resp = self.client.get('/api/v2/keyvalue/?keystore=fake-hostname2', follow=True)
        self.assertEqual(json.loads(resp.content)['host:fake-hostname1:nic.0.ipv4_address.0'], '10.99.32.3')

        resp = self.client.get('/api/v2/keyvalue/?key=cluster_owner', follow=True)
        self.assertEqual(json.loads(resp.content)['truth:test:cluster_owner'], 'The Cluster Owner')

        resp = self.client.get('/api/v2/keyvalue/?value=10.99.32.3', follow=True)
        self.assertEqual(json.loads(resp.content)['host:fake-hostname1:nic.0.ipv4_address.0'], '10.99.32.3')

    def test_search_by_asset_tag(self):
        resp = self.client.get('/api/v2/system/3/', {'search':True, 'asset_tag':'65432'}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.content)[0]['asset_tag'], '65432')
        self.assertEqual(json.loads(resp.content)[0]['hostname'], 'fake-hostname2')

    def test_search_by_serial(self):
        resp = self.client.get('/api/v2/system/3/', {'search':True, 'serial':'39993'}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.content)[0]['serial'], '39993')
        self.assertEqual(json.loads(resp.content)[0]['hostname'], 'fake-hostname1')

    def test_search_by_serial_and_asset_tag_not_found(self):
        resp = self.client.get('/api/v2/system/3/', {'search':True, 'serial':'39993', 'asset_tag':'99999asdf'}, follow=True)
        self.assertEqual(resp.status_code, 404)

    def test_search_by_system_rack(self):
        resp = self.client.get('/api/v2/system/3/', {'search':True, 'system_rack_id':'1'}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.content)[0]['hostname'], 'fake-hostname1')

    def test_search_by_system_rack_and_rack_order(self):
        resp = self.client.get('/api/v2/system/3/', {'search':True, 'system_rack_id':'1', 'rack_order':'1.00'}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.content)[0]['hostname'], 'fake-hostname1')

    def test_search_by_system_rack_and_rack_order_not_found(self):
        resp = self.client.get('/api/v2/system/3/', {'search':True, 'system_rack_id':'1', 'rack_order':'2.00'}, follow=True)
        self.assertEqual(resp.status_code, 404)
        
    def test_search_by_system_rack_and_serial(self):
        resp = self.client.get('/api/v2/system/3/', {'search':True, 'system_rack_id':'1', 'serial':'39993'}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.content)[0]['hostname'], 'fake-hostname1')

    def test_search_by_system_switch_ports(self):
        resp = self.client.get('/api/v2/system/3/', {'search':True, 'switch_ports':'101.02'}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.content)[0]['hostname'], 'fake-hostname1')

    def test_search_by_system_switch_ports_not_found(self):
        resp = self.client.get('/api/v2/system/3/', {'search':True, 'switch_ports':'shouldnteverhavethisasaswitchport101.02'}, follow=True)
        self.assertEqual(resp.status_code, 404)

    def test_search_by_system_rack_and_serial_not_found(self):
        resp = self.client.get('/api/v2/system/3/', {'search':True, 'system_rack_id':'1', 'serial':'39993asdf'}, follow=True)
        self.assertEqual(resp.status_code, 404)

class DHCPApi(TestCase):
    fixtures = ['testdata.json']

    def setup(self):
        self.client = Client()

    def test_get_single_scope(self):
        resp = self.client.get('/api/v2/keyvalue/?key_type=dhcp_scopes', follow=True)
        scope_list = json.loads(resp.content)
        self.assertEqual(scope_list[0]['dhcp.is_scope'], 'True')
        self.assertEqual(scope_list[0]['dhcp.scope.start'], '10.0.1.0')
        self.assertEqual(scope_list[0]['dhcp.scope.end'], '10.0.1.255')
        self.assertEqual(scope_list[0]['dhcp.scope.name'], 'phx-vlan73')

    def test_get_second_scope(self):
        resp = self.client.get('/api/v2/keyvalue/?key_type=dhcp_scopes', follow=True)
        scope_list = json.loads(resp.content)
        """self.assertEqual(scope_list[1]['dhcp.is_scope'], 'True')
        self.assertEqual(scope_list[1]['dhcp.scope.start'], '10.0.0.0')
        self.assertEqual(scope_list[1]['dhcp.scope.end'], '10.0.0.255')
        self.assertEqual(scope_list[1]['dhcp.scope.name'], 'phx-vlan81')"""

    def test_get_multiple_scopes(self):
        resp = self.client.get('/api/v2/keyvalue/?key_type=dhcp_scopes', follow=True)
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
        resp = self.client.get('/api/v2/keyvalue/?key_type=system_by_scope&scope=phx-vlan73', follow=True)
        system_list = json.loads(resp.content)
        self.assertEqual(system_list[0]['nic.0.mac_address.0'],'00:00:00:00:00:AA')
        self.assertEqual(system_list[0]['nic.0.ipv4_address.0'],'10.99.32.1')
        self.assertEqual(system_list[0]['nic.1.mac_address.0'],'00:00:00:00:00:BB')
        self.assertEqual(system_list[0]['nic.1.ipv4_address.0'],'10.99.32.2')

    def test_get_adapters_by_system(self):
        resp = self.client.get(reverse('api_v2_keyvalue_get'), {'key_type': 'adapters_by_system', 'system':'fake-hostname2'}, follow=True)
        system_list = json.loads(resp.content)
        self.assertEqual(resp.status_code,  200)
        #print system_list
    def test_delete_network_adapter(self):
        resp = self.client.delete('/api/v2/keyvalue/1/', {'system_hostname':'fake-hostname2', 'adapter_number':'0', 'key_type':'delete_network_adapter'}, follow=True)
        #print "The content is %s" % resp.content

    def test_add_dhcp_scope_via_api(self):
        ScheduledTask.objects.all().delete()
        self.assertEqual(len(ScheduledTask.objects.all()), 0)
        resp = self.client.post('/en-US/api/v2/dhcp/phx1-vlan73/add_scheduled_task/', follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(ScheduledTask.objects.all()), 1)
        self.assertEqual(ScheduledTask.objects.all()[0].type, 'dhcp')

    def test_get_adapters_by_system_and_scope(self):
        """
            Get a list of all the adapters in this dhcp scope by system.
            Should not include systems without a nic.X.ipv4_address.9 value
        """
        resp = self.client.get(reverse('api_v2_keyvalue_get'), {'key_type': 'adapters_by_system_and_scope', 'dhcp_scope': 'phx-vlan73', 'system':'fake-hostname2'}, follow=True)
        self.assertEqual(resp.status_code, 200)
        system_list = json.loads(resp.content)
        self.assertEqual(len(system_list), 2)
        """
            Delete a nic.0.ipv4_address.0 key/value pair
            There should now only be one adapter available
        """
        KeyValue.objects.get(id=8).delete()
        resp = self.client.get(reverse('api_v2_keyvalue_get'), {'key_type': 'adapters_by_system_and_scope', 'dhcp_scope': 'phx-vlan73', 'system':'fake-hostname2'}, follow=True)
        self.assertEqual(resp.status_code, 200)
        system_list = json.loads(resp.content)
        self.assertEqual(len(system_list), 1)


    def test_delete_dhcp_scope_via_api(self):
        ScheduledTask.objects.all().delete()
        self.assertEqual(len(ScheduledTask.objects.all()), 0)
        resp = self.client.post('/en-US/api/v2/dhcp/phx1-vlan73/add_scheduled_task/', follow=True)
        self.assertEqual(len(ScheduledTask.objects.all()), 1)
        resp = self.client.delete('/en-US/api/v2/dhcp/phx1-vlan73/remove_scheduled_task/', follow=True)
        self.assertEqual(len(ScheduledTask.objects.all()), 0)

class TestReverseDNSApi(TestCase):
    fixtures = ['testdata.json']

    def setup(self):
        self.client = Client()

    def test_get_single_reverse_zone_names_with_descriptions(self):
        resp = self.client.get('/api/v2/reverse_dns/1/get_reverse_dns_zones_with_names/', follow=True)
        self.assertEqual(resp.status_code, 200)
        scope_list = json.loads(resp.content)
        self.assertEqual(len(scope_list), 2)
        self.assertEqual(scope_list[0]['name'], 'phx1-32.8.10.in-addr.arpa')
        self.assertEqual(scope_list[0]['description'], '10.99.32.0 reverse dns zone')
        self.assertEqual(scope_list[1]['name'], 'phx1-33.8.10.in-addr.arpa')
        self.assertEqual(scope_list[1]['description'], '10.99.33.0 reverse dns zone')

    def test_get_system_by_reverse_dns_zone(self):
        resp = self.client.get('/api/v2/keyvalue/?key_type=system_by_reverse_dns_zone&zone=phx1-32.8.10.in-addr.arpa', follow=True)
        self.assertEqual(resp.status_code, 200)
        system_list = json.loads(resp.content)
        self.assertEqual(len(system_list), 2)
        self.assertEqual(system_list[0]['nic.0.ipv4_address.0'],'10.99.32.1')
        self.assertEqual(system_list[0]['hostname'],'fake-hostname2')
        self.assertEqual(system_list[0]['nic.1.ipv4_address.0'],'10.99.32.2')
        self.assertEqual(system_list[1]['nic.0.ipv4_address.0'],'10.99.32.3')
        self.assertEqual(system_list[1]['hostname'],'fake-hostname1')

class KeyValueApi(TestCase):
    fixtures = ['testdata.json']

    def setup(self):
        self.client = Client()

    def test_get_adapters_by_system(self):
        resp = self.client.get('/api/v2/keyvalue/3/', {'key_type':'adapters_by_system','system':'fake-hostname2'}, follow=True)

    def test_keyvalue_set_invalid_ip(self):
        resp = self.client.put('/en-US/api/v2/keyvalue/3/', {'system_id':'2', 'value':'1.1.1asdfasdf.1','key':'nic.0.ipv4_address.0'}, follow=True)
        self.assertEqual(resp.status_code, 401)

    def test_keyvalue_set_valid_ip(self):
        resp = self.client.put('/en-US/api/v2/keyvalue/3/', {'system_id':'2', 'value':'10.99.32.44','key':'nic.0.ipv4_address.0'}, follow=True)
        self.assertEqual(resp.status_code, 200)

    def test_keyvalue_duplicate_update_ip(self):
        resp = self.client.put('/en-US/api/v2/keyvalue/3/', {'system_id':'2', 'value':'10.99.32.1','key':'nic.0.ipv4_address.0'}, follow=True)
        resp = self.client.put('/en-US/api/v2/keyvalue/2/', {'system_id':'2', 'value':'10.99.32.1','key':'nic.0.ipv4_address.0'}, follow=True)
        self.assertEqual(resp.status_code, 401)

    def test_keyvalue_duplicate_create_ip(self):
        resp = self.client.put('/en-US/api/v2/keyvalue/3/', {'system_id':'2', 'value':'10.99.32.1','key':'nic.0.ipv4_address.0'}, follow=True)
        resp = self.client.post('/en-US/api/v2/keyvalue/4/', {'system_id':'2', 'value':'10.99.32.1','key':'nic.0.ipv4_address.0'}, follow=True)
        self.assertEqual(resp.status_code, 401)

    def test_keyvalue_set_invalid_mac_address(self):
        resp = self.client.put('/en-US/api/v2/keyvalue/3/', {'system_id':'2', 'value':'asdfsadfsadf','key':'nic.0.mac_address.0'}, follow=True)
        self.assertEqual(resp.status_code, 401)

    def test_keyvalue_set_valid_mac_address(self):
        resp = self.client.put('/en-US/api/v2/keyvalue/7/', {'system_id':'2', 'value':'00:00:00:00:00:00','key':'nic.0.mac_address.0'}, follow=True)
        #print resp.content
        self.assertEqual(resp.status_code, 200)

    def test_keyvalue_set_invalid_is_dhcp_scope(self):
        resp = self.client.put('/en-US/api/v2/keyvalue/3/', {'system_id':'2', 'value':'true','key':'is_dhcp_scope'}, follow=True)
        self.assertEqual(resp.status_code, 401)


    def test_keyvalue_set_invalid_dhcp_scope_start(self):
        resp = self.client.put('/en-US/api/v2/keyvalue/3/', {'system_id':'2', 'value':'1.1.1asdfasdf.1','key':'dhcp.scope.start'}, follow=True)
        self.assertEqual(resp.status_code, 401)

    """def test_keyvalue_set_valid_dhcp_scope_start(self):
        resp = self.client.put('/en-US/api/v2/keyvalue/3/', {'system_id':'2', 'value':'10.99.32.1','key':'dhcp.scope.start'}, follow=True)
        self.assertEqual(resp.status_code, 200)"""

    def test_keyvalue_set_invalid_dhcp_scope_end(self):
        resp = self.client.put('/en-US/api/v2/keyvalue/3/', {'system_id':'2', 'value':'1.1.1asdfasdf.1','key':'dhcp.scope.end'}, follow=True)
        self.assertEqual(resp.status_code, 401)

    """def test_keyvalue_set_valid_dhcp_scope_end(self):
        resp = self.client.put('/en-US/api/v2/keyvalue/3/', {'system_id':'2', 'value':'10.99.32.1','key':'dhcp.scope.end'}, follow=True)
        self.assertEqual(resp.status_code, 200)"""


    def test_keyvalue_set_invalid_dhcp_pool_start(self):
        resp = self.client.put('/en-US/api/v2/keyvalue/3/', {'system_id':'2', 'value':'1.1.1asdfasdf.1','key':'dhcp.pool.start'}, follow=True)
        self.assertEqual(resp.status_code, 401)

    """def test_keyvalue_set_valid_dhcp_pool_start(self):
        resp = self.client.put('/en-US/api/v2/keyvalue/3/', {'system_id':'2', 'value':'10.99.32.1','key':'dhcp.pool.start'}, follow=True)
        self.assertEqual(resp.status_code, 200)"""

    def test_keyvalue_set_invalid_dhcp_pool_end(self):
        resp = self.client.put('/en-US/api/v2/keyvalue/3/', {'system_id':'2', 'value':'1.1.1asdfasdf.1','key':'dhcp.pool.end'}, follow=True)
        self.assertEqual(resp.status_code, 401)

    """def test_keyvalue_set_valid_dhcp_pool_end(self):
        resp = self.client.put('/en-US/api/v2/keyvalue/3/', {'system_id':'2', 'value':'10.99.32.1','key':'dhcp.pool.end'}, follow=True)
        self.assertEqual(resp.status_code, 200)"""

    def test_keyvalue_set_invalid_dhcp_scope_netmask(self):
        resp = self.client.put('/en-US/api/v2/keyvalue/3/', {'system_id':'2', 'value':'1.1.1asdfasdf.1','key':'dhcp.scope.start'}, follow=True)
        self.assertEqual(resp.status_code, 401)

    """def test_keyvalue_set_valid_dhcp_scope_netmask(self):
        resp = self.client.put('/en-US/api/v2/keyvalue/3/', {'system_id':'2', 'value':'10.99.32.1','key':'dhcp.scope.start'}, follow=True)
        self.assertEqual(resp.status_code, 200)"""

    def test_keyvalue_set_invalid_dhcp_ntp_server(self):
        resp = self.client.put('/en-US/api/v2/keyvalue/3/', {'system_id':'2', 'value':'1.1.1asdfasdf.1','key':'dhcp.option.ntp_server.0'}, follow=True)
        self.assertEqual(resp.status_code, 401)

    """def test_keyvalue_set_valid_dhcp_ntp_server(self):
        resp = self.client.put('/en-US/api/v2/keyvalue/3/', {'system_id':'2', 'value':'10.99.32.1','key':'dhcp.option.ntp_server.0'}, follow=True)
        self.assertEqual(resp.status_code, 200)"""
