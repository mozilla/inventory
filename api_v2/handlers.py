from piston.handler import BaseHandler, rc
from systems.models import System, RelengDistro, SystemRack,SystemStatus,NetworkAdapter,KeyValue
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
