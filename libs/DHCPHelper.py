from systems.models import ScheduledTask, KeyValue, System
import re


class DHCPHelper(object):
    scopes_to_generate = []

    def __init__(self):
        pass

    def get_scopes_to_generate(self):
        return ScheduledTask.objects.get_all_dhcp()

    def systems_by_scope(self, scope):
        keyvalue_pairs = KeyValue.objects.filter(key__contains='dhcp_scope',value=scope).filter(key__startswith='nic.')
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
        return tmp_list

    def adapters_by_system_and_scope(self, system, scope):
        dhcp_scope = scope
        system = System.objects.get(hostname=system)
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
                ip_address_match = 'nic.%s.ipv4_address.0' % matches.group(1)
                if matches.group(1) not in adapter_ids and ip_address_match in tmp_dict and dhcp_scope_match in tmp_dict and tmp_dict[dhcp_scope_match] == dhcp_scope:
                    adapter_ids.append(matches.group(1))
        adapter_ids.sort()
        for a in adapter_ids:
            adapter_name = ''
            mac_address = ''
            dhcp_hostname = ''
            dhcp_filename = ''
            dhcp_domain_name = ''
            ipv4_address = ''
            dhcp_domain_name_servers = ''
            if 'nic.%s.ipv4_address.0' % a in tmp_dict:
                ipv4_address = tmp_dict['nic.%s.ipv4_address.0' % a]
            if 'nic.%s.name.0' % a in tmp_dict:
                adapter_name = tmp_dict['nic.%s.name.0' % a]
            if 'nic.%s.mac_address.0' % a in tmp_dict:
                mac_address = tmp_dict['nic.%s.mac_address.0' % a]
            if 'nic.%s.dhcp_hostname.0' % a in tmp_dict and 'nic.%s.option_hostname.0' % a not in tmp_dict:
                dhcp_hostname = tmp_dict['nic.%s.dhcp_hostname.0' % a]
            if  'nic.%s.option_hostname.0' % a in tmp_dict:
                dhcp_hostname = tmp_dict['nic.%s.option_hostname.0' % a]
            if 'nic.%s.dhcp_filename.0' % a in tmp_dict:
                dhcp_filename = tmp_dict['nic.%s.dhcp_filename.0' % a]
            if 'nic.%s.dhcp_domain_name.0' % a in tmp_dict:
                dhcp_domain_name = tmp_dict['nic.%s.dhcp_domain_name.0' % a]
            if 'nic.%s.dhcp_domain_name_servers.0' % a in tmp_dict:
                dhcp_domain_name_servers = tmp_dict['nic.%s.dhcp_domain_name_servers.0' % a]
            final_list.append({'system_hostname':system.hostname, 'ipv4_address':ipv4_address,  'adapter_name':adapter_name, 'mac_address':mac_address, 'option_hostname': dhcp_hostname, 'dhcp_hostname':dhcp_hostname, 'dhcp_filename':dhcp_filename, 'dhcp_domain_name':dhcp_domain_name, 'dhcp_domain_name_servers':dhcp_domain_name_servers})
        return final_list
