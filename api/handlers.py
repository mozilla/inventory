from piston.handler import BaseHandler, rc
from systems.models import System, SystemRack,SystemStatus,NetworkAdapter,KeyValue,ScheduledTask
from truth.models import Truth, KeyValue as TruthKeyValue
from dhcp.DHCP import DHCP as DHCPInterface
from dhcp.models import DHCP
from MacroExpansion import MacroExpansion
from KeyValueTree import KeyValueTree
import re
try:
    import json
except:
    from django.utils import simplejson as json
from django.test.client import Client
from settings import API_ACCESS
class DHCPHandler(BaseHandler):
    allowed_methods = API_ACCESS
    model = System
    #fields = ('id', 'asset_tag', 'oob_ip', 'hostname', 'operating_system', ('system_status',('status', 'id')))
    exclude = ()
    def read(self, request, dhcp_scope=None, dhcp_action=None):
        if dhcp_scope and dhcp_action == 'get_scopes':
            tasks = []
            for task in ScheduledTask.objects.get_all_dhcp():
                tasks.append(task.task)
            ScheduledTask.objects.delete_all_dhcp()
            return tasks
        if dhcp_scope and dhcp_action == 'view_hosts':
            scope_options = []
            client = Client()
            hosts = json.loads(client.get('/api/keyvalue/?key_type=system_by_scope&scope=%s' % dhcp_scope, follow=True).content)
            #print hosts
            adapter_list = []
            for host in hosts:
                if 'hostname' in host:
                    the_url = '/api/keyvalue/?key_type=adapters_by_system_and_scope&dhcp_scope=%s&system=%s' % (dhcp_scope, host['hostname'], follow=True)
                    try:
                        adapter_list.append(json.loads(client.get(the_url).content))
                    except:
                        pass
            d = DHCPInterface(scope_options, adapter_list)
            return d.get_hosts()

class SystemHandler(BaseHandler):
    allowed_methods = API_ACCESS
    model = System
    #fields = ('id', 'asset_tag', 'oob_ip', 'hostname', 'operating_system', ('system_status',('status', 'id')))
    exclude = ()
    def read(self, request, system_id=None):
        model = System
        base = model.objects
        #return base.get(id=453)
        if system_id:
            try:
                try:
                    s = System.objects.get(id=system_id)
                except:
                    pass
                try:
                    s = System.objects.get(hostname=system_id)
                except:
                    pass
                if s is not None:
                    return s
            except:
                resp = rc.NOT_FOUND
                return resp
        else:
            #return base.filter(id_gt=400) # Or base.filter(...)
            return base.all()
    def create(self, request, system_id=None):
        s = System()
        s.hostname = system_id 
        try:
            s.save()
            resp = rc.CREATED
            resp.write('json = {"id":%i, "hostname":"%s"}' % (s.id, s.hostname))
        except:
            resp = rc.BAD_REQUEST
            resp.write('Unable to Create Host')
            
        return resp

    def delete(self, request, system_id=None):
        try:
            s = System.objects.get(id=system_id)
            id = s.id
            hostname = s.hostname
            s.delete()
            resp = rc.ALL_OK
            resp.write('json = {"id":%i, "hostname":"%s"}' % (id, hostname))
        except:
            resp = rc.NOT_FOUND
            resp.write("Unable to find system")

        return resp
    def update(self, request, system_id=None):
        model = System
    	if request.method == 'PUT':
            try:
                try:
                    s = System.objects.get(id=system_id)
                except:
                    pass
                try:
                    s = System.objects.get(hostname=system_id)
                except:
                    pass
                if 'system_status' in request.POST:
                    try:
                        ss = SystemStatus.objects.get(id=request.POST['system_status'])
                        s.system_status = ss
                    except:
                        resp = rc.NOT_FOUND
                        resp.write("System Status Not Found") 
                if 'system_rack' in request.POST:
                    try:
                        sr = SystemRack.objects.get(id=request.POST['system_rack'])
                        s.system_rack = sr
                    except:
                        pass
                        #resp = rc.NOT_FOUND
                        #resp.write("System Rack Not Found") 
                if 'location' in request.POST:
                    s.location = request.POST['location']
                if 'asset_tag' in request.POST:
                    s.asset_tag = request.POST['asset_tag']
                if 'serial' in request.POST:
                    s.serial = request.POST['serial']

                if 'oob_ip' in request.POST:
                    s.oob_ip = request.POST['oob_ip']

                if 'hostname' in request.POST:
                    s.hostname = request.POST['hostname']

                if 'notes' in request.POST:
                    s.notes = request.POST['notes']
                s.save()
                resp = rc.ALL_OK
                resp.write('json = {"id":%i, "hostname":"%s"}' % (s.id, s.hostname))
            except:
                resp = rc.NOT_FOUND
                resp.write("System Updated")
            return resp
class TruthHandler(BaseHandler):
    allowed_methods = API_ACCESS
    def create(self, request, key_value_id=None):
        n = KeyValue()
        if 'truth_id' in request.POST:
            truth = Truth.objects.get(id=request.POST['truth_id'])
            n.system = system
        if 'key' in request.POST:
            n.key = request.POST['key']
        if 'value' in request.POST:
            n.value = request.POST['value']
        try:
            n.save()
            resp = rc.ALL_OK
            resp.write('json = {"id":%i}' % (n.id))
        except:
            resp = rc.NOT_FOUND
            resp.write('Unable to Create Key/Value Pair')
        return resp

    def update(self, request, key_value_id=None):
        n = KeyValue.objects.get(id=key_value_id,key=request.POST['key'])
        if 'system_id' in request.POST:
            system = System.objects.get(id=request.POST['system_id'])
            n.system = system
        if 'value' in request.POST:
            n.value = request.POST['value']
        try:
            n.save()
            resp = rc.ALL_OK
            resp.write('json = {"id":%i}' % (n.id))
        except:
            resp = rc.NOT_FOUND
            resp.write('Unable to Create Key/Value Pair')
        return resp
    def read(self, request, key_value_id=None):
        base = Truth.expanded_objects
        if 'key' in request.GET:
            base = base.filter(key=request.GET['key'])
        if 'value' in request.GET:
            base = base.filter(value=request.GET['value'])
        if 'id' in request.GET:
            base = base.filter(id=request.GET['id'])
        if key_value_id is not None:
            base = base.filter(id=key_value_id)
        if 'truth_id' in request.GET:
            try:
                truth = System.objects.get(id=request.GET['truth_id'])
                base = base.filter(truth=truth)
            except Exception, e:
                resp = rc.NOT_FOUND
                return resp

        for row in base:
            matches = re.match("\$\{(.*)\}", row.value)
            if matches is not None:
                m = MacroExpansion(matches.group(1))
                row.value = m.output()
        return base
    def delete(self, request, key_value_id=None):
        try:
            n = KeyValue.objects.get(id=key_value_id)
            n.delete()
            resp = rc.ALL_OK
            resp.write('json = {"id":"%s"}' % str(key_value_id))
        except:
            resp = rc.NOT_FOUND
        return resp
class KeyValueHandler(BaseHandler):
    allowed_methods = API_ACCESS
    def create(self, request, key_value_id=None):
        if 'system_id' in request.POST:
            n = KeyValue()
            system = System.objects.get(id=request.POST['system_id'])
            n.system = system
            if 'key' in request.POST:
                n.key = request.POST['key']
            if 'value' in request.POST:
                n.value = request.POST['value']
            try:
                n.save()
                resp = rc.ALL_OK
                resp.write('json = {"id":%i}' % (n.id))
            except:
                resp = rc.NOT_FOUND
                resp.write('Unable to Create Key/Value Pair')
            return resp
        if 'truth_name' in request.POST:
            n = TruthKeyValue()
            truth = Truth.objects.get(name=request.POST['truth_name'])
            n.truth = truth
            if 'key' in request.POST:
                n.key = request.POST['key']
            if 'value' in request.POST:
                n.value = request.POST['value']
            try:
                n.save()
                resp = rc.ALL_OK
                resp.write('json = {"id":%i}' % (n.id))
            except:
                resp = rc.NOT_FOUND
                resp.write('Unable to Create Key/Value Pair')
            return resp

    def update(self, request, key_value_id=None):
        if 'system_id' in request.POST:
            n = KeyValue.objects.get(id=key_value_id,key=request.POST['key'])
            system = System.objects.get(id=request.POST['system_id'])
            n.system = system
            if 'value' in request.POST:
                n.value = request.POST['value']
            try:
                n.save()
                resp = rc.ALL_OK
                resp.write('json = {"id":%i}' % (n.id))
            except:
                resp = rc.NOT_FOUND
                resp.write('Unable to Create Key/Value Pair')
            return resp
        else:
            try:
                truth = Truth.objects.get(name=key_value_id)
                n = TruthKeyValue.objects.get(truth=truth,key=request.POST['key'])
                if 'value' in request.POST:
                    n.value = request.POST['value']
            except:
                pass
            try:
                n.save()
                resp = rc.ALL_OK
                resp.write('json = {"id":%i}' % (n.id))
            except:
                resp = rc.NOT_FOUND
                resp.write('Unable to Create Key/Value Pair')
            return resp

    def read(self, request, key_value_id=None):
        #if keystore get var is set return the whole keystore
        if 'keystore' in request.GET:
            #if key get var is set return the keystore based on the existance of this key
            if 'key' in request.GET:
                base = KeyValue.objects.filter(key=request.GET['keystore']).filter(keyvalue_set__contains=request.GET['key'])
                tmp_list = []
                for row in base:
                    matches = re.match("\$\{(.*)\}", row.value)
                    if matches is not None:
                        m = MacroExpansion(matches.group(1))
                        row.value = m.output()
                for r in base:
                    key_name = 'host:%s:%s' % (r.system.hostname, r.key)
                    tmp_list[key_name] = r.value
            if 'key' not in request.GET:
                tree = KeyValueTree(request.GET['keystore']).final
                return tree
        elif 'key_type' in request.GET:
            key_type = request.GET['key_type']
            tmp_list = []
            if key_type == 'dhcp_scopes':
                #Get keystores from truth that have dhcp.is_scope = True
                base = TruthKeyValue.objects.filter(key='dhcp.is_scope',value='True')
                #Iterate through the list and get all of the key/value pairs
                for row in base:
                    keyvalue = TruthKeyValue.objects.filter(truth=row.truth)
                    tmp_dict = {}
                    for kv in keyvalue:
                        tmp_dict[kv.key] = kv.value
                    tmp_list.append(tmp_dict)
                return tmp_list

            if key_type == 'system_by_scope':
                #Get keystores from truth that have dhcp.is_scope = True
                keyvalue_pairs = KeyValue.objects.filter(key__contains='dhcp_scope',value=request.GET['scope']).filter(key__startswith='nic.')
                #Iterate through the list and get all of the key/value pairs
                tmp_list = []
                for row in keyvalue_pairs:
                    keyvalue = KeyValue.objects.filter(system=row.system)
                    tmp_dict = {}
                    for kv in keyvalue:
                        tmp_dict[kv.key] = kv.value
                    tmp_dict['hostname'] = row.system.hostname
                    appendable = True
                    for the_items in tmp_list:
                        if 'hostname' not in the_items:
                            appendable = True
                        elif the_items['hostname'] == row.system.hostname:
                            appendable = False
                    if appendable is True:
                        tmp_list.append(tmp_dict)
                    #tmp_list = list(set(tmp_list))
                return tmp_list
            if key_type == 'adapters_by_system':
                #Get keystores from truth that have dhcp.is_scope = True
                system = System.objects.get(hostname=request.GET['system'])
                keyvalue_pairs = KeyValue.objects.filter(key__startswith='nic.').filter(system=system).order_by('key')
                #Iterate through the list and get all of the key/value pairs
                tmp_dict = {}
                adapter_ids = []
                final_list = []
                for kv in keyvalue_pairs:
                    tmp_dict[kv.key] = kv.value
                for k in tmp_dict.iterkeys():
                    matches = re.match('nic\.(\d+).*',k)
                    if matches.group is not None:
                        if matches.group(1) not in adapter_ids:
                            adapter_ids.append(matches.group(1))
                adapter_ids.sort()
                for a in adapter_ids:
                    adapter_name = ''
                    mac_address = ''
                    dhcp_hostname = ''
                    dhcp_filename = ''
                    ipv4_address = ''
                    option_domain_name = ''
                    if 'nic.%s.ipv4_address.0' % a in tmp_dict:
                        ipv4_address = tmp_dict['nic.%s.ipv4_address.0' % a]
                    if 'nic.%s.name.0' % a in tmp_dict:
                        adapter_name = tmp_dict['nic.%s.name.0' % a]
                    if 'nic.%s.mac_address.0' % a in tmp_dict:
                        mac_address = tmp_dict['nic.%s.mac_address.0' % a]
                    if 'nic.%s.dhcp_hostname.0' % a in tmp_dict:
                        dhcp_hostname = tmp_dict['nic.%s.dhcp_hostname.0' % a]
                    if 'nic.%s.dhcp_filename.0' % a in tmp_dict:
                        dhcp_filename = tmp_dict['nic.%s.dhcp_filename.0' % a]
                    try:
                        final_list.append({
                            'system_hostname':system.hostname,
                            'ipv4_address':ipv4_address,
                            'adapter_name':adapter_name,
                            'mac_address':mac_address,
                            'dhcp_hostname':dhcp_hostname,
                            'dhcp_filename':dhcp_filename}
                            )
                    except:
                        pass
                #tmp_list.append(tmp_dict)
                return final_list
            if key_type == 'adapters_by_system_and_scope':
                #Get keystores from truth that have dhcp.is_scope = True
                dhcp_scope = request.GET['dhcp_scope']
                system = System.objects.get(hostname=request.GET['system'])
                keyvalue_pairs = KeyValue.objects.filter(key__startswith='nic.').filter(system=system).order_by('key')
                #Iterate through the list and get all of the key/value pairs
                tmp_dict = {}
                adapter_ids = []
                final_list = []
                for kv in keyvalue_pairs:
                    tmp_dict[kv.key] = kv.value
                for k in tmp_dict.iterkeys():
                    matches = re.match('nic\.(\d+).*',k)
                    if matches.group is not None:
                        #if matches.group(1) not in adapter_ids and tmp_dict['nic.%s.dhcp_scope.0' % matches.group(1)] is not None and tmp_dict['nic.%s.dhcp_scope.0' % matches.group(1)] == dhcp_scope:
                        dhcp_scope_match = 'nic.%s.dhcp_scope.0' % matches.group(1)
                        if matches.group(1) not in adapter_ids and dhcp_scope_match in tmp_dict and tmp_dict[dhcp_scope_match] == dhcp_scope:
                            adapter_ids.append(matches.group(1))
                adapter_ids.sort()
                for a in adapter_ids:
                    adapter_name = ''
                    mac_address = ''
                    dhcp_hostname = ''
                    dhcp_filename = ''
                    dhcp_domain_name = ''
                    ipv4_address = ''
                    if 'nic.%s.ipv4_address.0' % a in tmp_dict:
                        ipv4_address = tmp_dict['nic.%s.ipv4_address.0' % a]
                    if 'nic.%s.name.0' % a in tmp_dict:
                        adapter_name = tmp_dict['nic.%s.name.0' % a]
                    if 'nic.%s.mac_address.0' % a in tmp_dict:
                        mac_address = tmp_dict['nic.%s.mac_address.0' % a]
                    if 'nic.%s.dhcp_hostname.0' % a in tmp_dict:
                        dhcp_hostname = tmp_dict['nic.%s.dhcp_hostname.0' % a]
                    if 'nic.%s.dhcp_filename.0' % a in tmp_dict:
                        dhcp_filename = tmp_dict['nic.%s.dhcp_filename.0' % a]
                    if 'nic.%s.dhcp_domain_name.0' % a in tmp_dict:
                        dhcp_domain_name = tmp_dict['nic.%s.dhcp_domain_name.0' % a]
                    final_list.append({'system_hostname':system.hostname, 'ipv4_address':ipv4_address,  'adapter_name':adapter_name, 'mac_address':mac_address, 'dhcp_hostname':dhcp_hostname, 'dhcp_filename':dhcp_filename, 'dhcp_domain_name':dhcp_domain_name})
                #tmp_list.append(tmp_dict)
                return final_list
        elif 'key' in request.GET and request.GET['key'] > '':
            tmp_list = {}
            try:
                base = KeyValue.objects.filter(key=request.GET['key'])
                for row in base:
                    matches = re.match("\$\{(.*)\}", row.value)
                    if matches is not None:
                        m = MacroExpansion(matches.group(1))
                        row.value = m.output()
                for r in base:
                    key_name = 'host:%s:%s' % (r.system.hostname, r.key)
                    tmp_list[key_name] = r.value
            except Exception, e:
                pass
            try:
                base = TruthKeyValue.objects.filter(key=request.GET['key'])
                for row in base:
                    matches = re.match("\$\{(.*)\}", row.value)
                    if matches is not None:
                        m = MacroExpansion(matches.group(1))
                        row.value = m.output()
                for r in base:
                    key_name = 'truth:%s:%s' % (r.truth.name, r.key)
                    tmp_list[key_name] = r.value
            except Exception, e:
                pass

            return tmp_list
        elif 'value' in request.GET:
            tmp_list = {}
            try:
                base = KeyValue.objects.filter(value=request.GET['value'])
                for row in base:
                    matches = re.match("\$\{(.*)\}", row.value)
                    if matches is not None:
                        m = MacroExpansion(matches.group(1))
                        row.value = m.output()
                for r in base:
                    key_name = 'host:%s:%s' % (r.system.hostname, r.key)
                    tmp_list[key_name] = r.value
            except Exception, e:
                pass
            try:
                base = TruthKeyValue.objects.filter(value=request.GET['value'])
                for row in base:
                    matches = re.match("\$\{(.*)\}", row.value)
                    if matches is not None:
                        m = MacroExpansion(matches.group(1))
                        row.value = m.output()
                for r in base:
                    key_name = 'truth:%s:%s' % (r.truth.name, r.key)
                    tmp_list[key_name] = r.value
            except Exception, e:
                pass

            return tmp_list
        #print tree
        """for t in tree:
            print '%s %s' % (t, tree[t])
        if 'system_id' in request.GET:
            base = KeyValue.expanded_objects
            if 'key' in request.GET:
                base = base.filter(key=request.GET['key'])
            if 'value' in request.GET:
                base = base.filter(value=request.GET['value'])
            if 'id' in request.GET:
                base = base.filter(id=request.GET['id'])
            if key_value_id is not None:
                base = base.filter(id=key_value_id)
            try:
                system = System.objects.get(id=request.GET['system_id'])
                base = base.filter(system=system)
            except Exception, e:
                resp = rc.NOT_FOUND
                return resp
            ##Recursirvely loop through to get all parents,siblings
            tmp_list = []
            for row in base:
                matches = re.match("\$\{(parent.*)\}", row.key)
                if matches is not None:
                    m = MacroExpansion(matches.group(1))
                    row.value = m.output()


            for row in base:
                matches = re.match("\$\{(.*)\}", row.value)
                if matches is not None:
                    m = MacroExpansion(matches.group(1))
                    row.value = m.output()
            return base
        if 'truth_id' in request.GET:
            base = TruthKeyValue.expanded_objects
            if 'key' in request.GET:
                base = base.filter(key=request.GET['key'])
            if 'value' in request.GET:
                base = base.filter(value=request.GET['value'])
            if 'id' in request.GET:
                base = base.filter(id=request.GET['id'])
            if key_value_id is not None:
                base = base.filter(id=key_value_id)
            try:
                truth = Truth.objects.get(id=request.GET['truth_id'])
                base = base.filter(truth=truth)
            except Exception, e:
                resp = rc.NOT_FOUND
                return resp

            for row in base:
                matches = re.match("\$\{(.*)\}", row.value)
                if matches is not None:
                    m = MacroExpansion(matches.group(1))
                    row.value = m.output()
            return base"""
    def delete(self, request, key_value_id=None):
        if 'key_type' in request.GET and request.GET['key_type'] == 'delete_all_network_adapters':
            #Get keystores from truth that have dhcp.is_scope = True
            try:
                system_hostname = request.GET['system_hostname']
                system = System.objects.get(hostname=system_hostname)
                KeyValue.objects.filter(key__startswith='nic', system=system).delete()
                resp = rc.ALL_OK
                resp.write('json = {"id":"0"}')
            except:
                resp = rc.NOT_FOUND
                resp.write('json = {"error_message":"Unable to Delete}')

            return resp
        if 'key_type' in request.GET and request.GET['key_type'] == 'delete_network_adapter':
            #Get keystores from truth that have dhcp.is_scope = True
            try:
                adapter_number = request.GET['adapter_number']
                system_hostname = request.GET['system_hostname']
                system = System.objects.get(hostname=system_hostname)
                KeyValue.objects.filter(key__startswith='nic.%s' % adapter_number, system=system).delete()
                #KeyValue.objects.filter(key__startswith='nic.0', system=system).delete()
                resp = rc.ALL_OK
                resp.write('json = {"id":"14"}')
            except:
                resp = rc.NOT_FOUND
                resp.write('json = {"error_message":"Unable to Delete}')

            return resp

        if 'key_type' not in request.GET:
            if 'system_id' in request.GET:
                try:
                    n = KeyValue.objects.get(id=key_value_id)
                    n.delete()
                    resp = rc.ALL_OK
                    resp.write('json = {"id":"%s"}' % str(key_value_id))
                except:
                    resp = rc.NOT_FOUND
                return resp
            if 'truth_id' in request.GET:
                try:
                    n = TruthKeyValue.objects.get(id=key_value_id)
                    n.delete()
                    resp = rc.ALL_OK
                    resp.write('json = {"id":"%s"}' % str(key_value_id))
                except:
                    resp = rc.NOT_FOUND
                return resp
        
        resp = rc.ALL_OK
        resp.write('json = {"id":"1"}')
        return resp

class NetworkAdapterHandler(BaseHandler):
    allowed_methods = API_ACCESS
    model = NetworkAdapter
    def create(self, request, network_adapter_id=None):
        n = NetworkAdapter()
        if 'system_id' in request.POST:
            n.system_id = request.POST['system_id']
        if 'mac_address' in request.POST:
            n.mac_address = request.POST['mac_address']
        if 'ip_address' in request.POST:
            n.ip_address = request.POST['ip_address']
        if 'adapter_name' in request.POST:
            n.adapter_name = request.POST['adapter_name']
        if 'option_file_name' in request.POST:
            n.option_file_name = request.POST['option_file_name']
        if 'option_domain_name' in request.POST:
            n.option_domain_name = request.POST['option_domain_name']
        if 'option_host_name' in request.POST:
            n.option_domain_name = request.POST['option_host_name']

        if 'dhcp_scope' in request.POST:
            try:
                n.dhcp_scope = DHCP.objects.get(scope_name=request.POST['dhcp_scope'])
            except:
                pass
        try:
            n.save()
            resp = rc.ALL_OK
            resp.write('json = {"id":%i}' % (n.id))
        except:
            resp = rc.NOT_FOUND
            resp.write('Unable to Create Host')
            
        return resp

    def read(self, request, network_adapter_id=None):
        base = NetworkAdapter.objects
        
        if network_adapter_id:
            return base.get(id=network_adapter_id)
        else:
            return base.all()

    def update(self, request, network_adapter_id=None):
    	if request.method == 'PUT':
            try:
                n = NetworkAdapter.objects.get(pk=network_adapter_id)
                if 'system_id' in request.POST:
                    n.system_id = request.POST['system_id']
                if 'mac_address' in request.POST:
                    n.mac_address = request.POST['mac_address']
                if 'ip_address' in request.POST:
                    n.ip_address = request.POST['ip_address']
                if 'adapter_name' in request.POST:
                    n.adapter_name = request.POST['adapter_name']
                if 'option_file_name' in request.POST:
                    n.file_name = request.POST['option_file_name']
                else:
                    n.file_name = ''
                if 'option_domain_name' in request.POST:
                    n.option_domain_name = request.POST['option_domain_name']
                else:
                    n.option_domain_name = ''
                if 'option_host_name' in request.POST:
                    n.option_host_name = request.POST['option_host_name']
                else:
                    n.option_host_name = ''
                if 'dhcp_scope' in request.POST:
                    try:
                        n.dhcp_scope = DHCP.objects.get(scope_name=request.POST['dhcp_scope'])
                    except:
                        pass
                n.save()
                resp = rc.ALL_OK
                resp.write('json = {"id":%i, "mac_address":"%s", "ip_address":"%s", "dhcp_scope":"%s", "system_id":"%s","option_file_name":"%s"}' % (n.id, n.mac_address, n.ip_address, n.dhcp_scope, n.system_id, n.file_name))
            except:
                resp = rc.NOT_FOUND
        else:
                resp = rc.NOT_FOUND
        return resp

    def delete(self, request, network_adapter_id=None):
        try:
            n = NetworkAdapter.objects.get(id=network_adapter_id)
            n.delete()
            network_adapter_id = str(network_adapter_id)
            resp = rc.ALL_OK
            resp.write('json = {"id":%s}' % (network_adapter_id))
        except:
            resp = rc.NOT_FOUND
        return resp

def fr(record):
    if not args:
        return [""]
    r = []
    for i in args[0]:
        for tmp in fr(args[1:]):
            r.append(i + tmp)
    return r
