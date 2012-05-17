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
    exclude = ()
    def read(self, request, dhcp_scope=None, dhcp_action=None):
        if dhcp_scope and dhcp_action == 'get_scopes':
            tasks = []
            for task in ScheduledTask.objects.get_all_dhcp():
                tasks.append(task.task)
            #ScheduledTask.objects.delete_all_dhcp()
            return tasks
        if dhcp_scope and dhcp_action == 'get_scopes_with_names':
            truths = Truth.objects.select_related().filter(keyvalue__key='is_dhcp_scope',keyvalue__value='True').order_by('name')

            truth_list = []
            for t in truths:
                truth_list.append({'name':t.name.strip(),'description':t.description.strip()})
            return truth_list
        if dhcp_scope and dhcp_action == 'view_hosts':
            scope_options = []
            client = Client()
            hosts = json.loads(client.get('/api/v2/keyvalue/?key_type=system_by_scope&scope=%s' % dhcp_scope, follow=True).content)
            #print hosts
            adapter_list = []
            for host in hosts:
                if 'hostname' in host:
                    the_url = '/api/v2/keyvalue/?key_type=adapters_by_system_and_scope&dhcp_scope=%s&system=%s' % (dhcp_scope, host['hostname'])
                    try:
                        adapter_list.append(json.loads(client.get(the_url, follow=True).content))
                    except:
                        pass
            d = DHCPInterface(scope_options, adapter_list)
            return d.get_hosts()

    def create(self, request, dhcp_scope=None, dhcp_action=None):
        if dhcp_scope and dhcp_action == 'add_scheduled_task':
            try:
                task = ScheduledTask(type='dhcp',task=dhcp_scope)
                task.save()
            except Exception, e:
                print e
            return rc.ALL_OK
        else:
            return rc.NOT_FOUND

    def delete(self, request, dhcp_scope=None, dhcp_action=None):

        if dhcp_scope and dhcp_action == 'remove_scheduled_task':
            try:
                task = ScheduledTask.objects.get(type='dhcp',task=dhcp_scope)
                task.delete()
            except:
                pass
            return rc.ALL_OK
