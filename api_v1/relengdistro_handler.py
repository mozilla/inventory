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


class RelengDistroHandler(BaseHandler):
    allowed_methods = API_ACCESS
    model = RelengDistro
    fields = ('id','distro_name')
    def create(self, request, releng_distro_id=None):
        rd = RelengDistro()
        rd.save()
        resp = rc.CREATED
        resp.write('Record Created')
        return resp

    def read(self, request, releng_distro_id=None):
        base = RelengDistro.objects
        
        if releng_distro_id:
            return base.get(pk=releng_distro_id)
        else:
            return base.all()

    def update(self, request, releng_distro_id=None):
        model = RelengDistro
    	if request.method == 'PUT':
            try:
                rd = model.objects.get(pk=releng_distro_id)
                rd.distro_name = request.POST['releng_distro_name']
                rd.save()
                resp = rc.ALL_OK
            except:
                resp = rc.NOT_FOUND
            return resp

    def delete(self, request, releng_distro_id=None):
        try:
            rd = RelengDistro.objects.get(pk=releng_distro_id)
            rd.delete()
            resp = rc.DELETED
            resp.write('Record Deleted')
        except:
            resp = rc.NOT_FOUND

        return resp
