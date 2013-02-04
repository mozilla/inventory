from piston.handler import BaseHandler, rc
from systems.models import System, SystemRack,SystemStatus,NetworkAdapter,KeyValue,ScheduledTask
from truth.models import Truth, KeyValue as TruthKeyValue
from MacroExpansion import MacroExpansion
from KeyValueTree import KeyValueTree
import re
try:
    import json
except:
    from django.utils import simplejson as json
from django.test.client import Client
from settings import API_ACCESS
class ReverseDNSHandler(BaseHandler):
    allowed_methods = API_ACCESS
    model = System
    #fields = ('id', 'asset_tag', 'oob_ip', 'hostname', 'operating_system', ('system_status',('status', 'id')))
    exclude = ()
    def read(self, request, reverse_dns_zone=None, reverse_dns_action=None):
        if reverse_dns_zone and reverse_dns_action == 'get_reverse_dns_zones':
            tasks = []
            for task in ScheduledTask.objects.get_all_reverse_dns():
                tasks.append(task.task)
            #ScheduledTask.objects.delete_all_reverse_dns()
            return tasks
        elif reverse_dns_zone and reverse_dns_action == 'get_reverse_dns_zones_with_names':
            truths = Truth.objects.select_related().filter(keyvalue__key='is_reverse_dns_zone',keyvalue__value='True')
            truth_list = []
            for t in truths:
                truth_list.append({'name':t.name.strip(),'description':t.description.strip()})
            return truth_list
        elif reverse_dns_zone and reverse_dns_action == 'view_hosts':
            scope_options = []
            client = Client()
            hosts = json.loads(client.get('/api/keyvalue/?key_type=system_by_zone&zone=%s' % reverse_dns_zone).content)
            #print hosts
            adapter_list = []
            for host in hosts:
                if 'hostname' in host:
                    the_url = '/api/keyvalue/?key_type=adapters_by_system_and_zone&reverse_dns_zone=%s&system=%s' % (reverse_dns_zone, host['hostname'])
                    try:
                        adapter_list.append(json.loads(client.get(the_url).content))
                    except:
                        pass
            #d = DHCPInterface(scope_options, adapter_list)
            #return d.get_hosts()
            return None
        else:
            resp = rc.NOT_FOUND
            resp.write("I'm sorry but I don't understand your request")
