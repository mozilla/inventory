from piston.handler import BaseHandler, rc
from systems.models import SystemRack
import re
try:
    import json
except:
    from django.utils import simplejson as json
from django.test.client import Client
from settings import API_ACCESS


class SystemRackHandler(BaseHandler):
    #allowed_methods = API_ACCESS
    allowed_methods = ('GET')
    #exclude = ('name','id', ('location', ('name', 'id') ) )
    fields = (
            ('id'),
            ('name'),
            ('site', ('id', 'full_name')),
        
        )
    model = SystemRack
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

    def read(self, request, system_rack_id=None):
        base = SystemRack.objects
        
        if system_rack_id:
            try:
                return base.order_by('id').get(id=system_rack_id)
            except:
                resp = rc.NOT_FOUND
                resp.write('Unable to find System Rack')
                return resp
        else:
            return base.order_by('id').all()

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
