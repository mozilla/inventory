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
