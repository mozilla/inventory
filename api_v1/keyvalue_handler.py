from piston.handler import BaseHandler, rc
from systems.models import System, SystemRack,SystemStatus,NetworkAdapter,KeyValue
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
        elif 'truth_name' in request.POST:
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
        else:
            resp = rc.NOT_FOUND
            resp.write('system_id or truth_name required')
    def build_validation_array(self):
        input_regex_array = []
        output_regex_array = []
        error_message_array = []

        ipv4_regex = re.compile(r'((2[0-5]|1[0-9]|[0-9])?[0-9]\.){3}((2[0-5]|1[0-9]|[0-9])?[0-9])')
        true_false_regex = re.compile('(^True$|^False$)')

        input_regex_array.append(re.compile('nic\.\d+\.ipv4_address\.\d+'))
        output_regex_array.append(ipv4_regex)
        error_message_array.append('Requires IP Address')

        input_regex_array.append(re.compile('^dhcp\.scope\.netmask$'))
        output_regex_array.append(ipv4_regex)
        error_message_array.append('Requires Subnet Mask')

        input_regex_array.append(re.compile('^is_dhcp_scope$'))
        output_regex_array.append(re.compile(true_false_regex))
        error_message_array.append('Requires True|False')

        input_regex_array.append(re.compile('^dhcp\.scope\.start$'))
        output_regex_array.append(re.compile(ipv4_regex))
        error_message_array.append('Requires IP Address')
        
        input_regex_array.append(re.compile('^dhcp\.scope\.end$'))
        output_regex_array.append(re.compile(ipv4_regex))
        error_message_array.append('Requires IP Address')

        input_regex_array.append(re.compile('^dhcp\.pool\.start$'))
        output_regex_array.append(re.compile(ipv4_regex))
        error_message_array.append('Requires IP Address')

        input_regex_array.append(re.compile('^dhcp\.pool\.end$'))
        output_regex_array.append(re.compile(ipv4_regex))
        error_message_array.append('Requires IP Address')

        input_regex_array.append(re.compile('^dhcp\.option\.ntp_server\.\d+$'))
        output_regex_array.append(re.compile(ipv4_regex))
        error_message_array.append('Requires IP Address')

        input_regex_array.append(re.compile('^dhcp\.dns_server\.\d+$'))
        output_regex_array.append(re.compile(ipv4_regex))
        error_message_array.append('Requires IP Address')

        input_regex_array.append(re.compile('^dhcp\.option_router\.\d+$'))
        output_regex_array.append(re.compile(ipv4_regex))
        error_message_array.append('Requires IP Address')

        input_regex_array.append(re.compile('^dhcp\.option\.subnet_mask\.\d+$'))
        output_regex_array.append(re.compile(ipv4_regex))
        error_message_array.append('Requires IP Address')

        input_regex_array.append(re.compile('^dhcp\.pool\.allow_booting\.\d+$'))
        output_regex_array.append(re.compile(true_false_regex))
        error_message_array.append('Requires True|False')
        
        input_regex_array.append(re.compile('^dhcp\.pool\.allow_bootp\.\d+$'))
        output_regex_array.append(re.compile(true_false_regex))
        error_message_array.append('Requires True|False')

        input_regex_array.append(re.compile('^nic\.\d+\.mac_address\.\d+$'))
        output_regex_array.append(re.compile('^([0-9a-f]{2}([:-]|$)){6}$', re.I))
        error_message_array.append('Requires Mac Address XX:XX:XX:XX:XX:XX')

        return input_regex_array, output_regex_array, error_message_array

    def validate(self, key, passed_value):
        error_message = None
        return_regex = None
        return_bool = True


        input_regex_array, output_regex_array, error_message_array = self.build_validation_array()
        ## Here we loop through all of the possible input validation array. If they key matches one, then we need to validate the value for the key/value pair
        for i in range(0, len(input_regex_array)):
            if input_regex_array[i].match(key):
                return_regex = output_regex_array[i]
                error_message = error_message_array[i];
                continue

        ## Check if we should validate the value portion of the key/value pair. No use validating it if the key doesn't require it
        if return_regex is not None:
            if return_regex.match(passed_value) is None:
                return_bool = False
            else:
                error_message = None


        return return_bool, error_message


    def update(self, request, key_value_id=None):
        ###TODO This whole method is not functioning correctly. Just for version 2. Not getting the system_id or truth_id from the poster firefox plugin
        if 'system_id' in request.POST:
            n = None
            key_validated, validation_error_string = self.validate(request.POST['key'], request.POST['value']) 
            if key_validated is False:
                resp = rc.FORBIDDEN
                resp.write('Validation Failed for %s %s' % (request.POST['key'], validation_error_string) )
                return resp
            try:
                n = KeyValue.objects.get(id=key_value_id,key=request.POST['key'])
                system = System.objects.get(id=request.POST['system_id'])
            except:
                resp = rc.NOT_FOUND
                resp.write('Neither system_id or truth_id found')

            if n is not None:
                n.system = system
            if 'value' in request.POST and n is not None:
                n.value = request.POST['value']
            if n is not None:
                try:
                    n.save()
                    resp = rc.ALL_OK
                    resp.write('json = {"id":%i}' % (n.id))
                except:
                    resp = rc.NOT_FOUND
                    resp.write('Unable to Create Key/Value Pair')
                return resp
        elif 'truth_id' in request.POST:
            try:
                truth = Truth.objects.get(name=key_value_id)
                na = TruthKeyValue.objects.get(truth=truth,key=request.POST['key'])
                if 'value' in request.POST:
                    n.value = request.POST['value']
            except:
                pass
            try:
                n.save()
                resp = rc.ALL_OK
                resp.write('json = {"id":%i}' % (n.id))
            except Exception, e:
                resp = rc.NOT_FOUND
                resp.write('Unable to Update Key/Value Pair %s' % e)
            return resp
        else:
            resp = rc.NOT_FOUND
            resp.write('Neither system_id or truth_id found')
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

            if key_type == 'system_by_reverse_dns_zone':

                #Get keystores from truth that have dhcp.is_scope = True
                keyvalue_pairs = KeyValue.objects.filter(key__contains='reverse_dns_zone',value=request.GET['zone']).filter(key__startswith='nic.')
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
            if key_type == 'adapters_by_system_and_zone':
                #Get keystores from truth that have dhcp.is_scope = True
                zone = request.GET['zone']
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
                        dhcp_scope_match = 'nic.%s.reverse_dns_zone.0' % matches.group(1)
                        if matches.group(1) not in adapter_ids and dhcp_scope_match in tmp_dict and tmp_dict[dhcp_scope_match] == zone:
                        #if matches.group(1) not in adapter_ids and 'nic.%s.dhcp_scope.0' % matches.group(1) in tmp_dict and tmp_dict['nic.%s.dhcp_scope.0' % matches.group(1)] == dhcp_scope:
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
                    final_list.append({'system_hostname':system.hostname, 'ipv4_address':ipv4_address})
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
                        dhcp_scope_match = 'nic.%s.dhcp_scope.0' % matches.group(1)
                        if matches.group(1) not in adapter_ids and dhcp_scope_match in tmp_dict and tmp_dict[dhcp_scope_match] == dhcp_scope:
                        #if matches.group(1) not in adapter_ids and 'nic.%s.dhcp_scope.0' % matches.group(1) in tmp_dict and tmp_dict['nic.%s.dhcp_scope.0' % matches.group(1)] == dhcp_scope:
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
                    if 'nic.%s.dhcp_hostname.0' % a in tmp_dict and 'nic.%s.option_hostname.0' % a not in tmp_dict:
                        dhcp_hostname = tmp_dict['nic.%s.dhcp_hostname.0' % a]
                    if  'nic.%s.option_hostname.0' % a not in tmp_dict:
                        dhcp_hostname = tmp_dict['nic.%s.option_hostname.0' % a]
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
