from KeyValueTree import KeyValueTree
from truth.models import KeyValue as TruthKeyValue, Truth
from systems.models import KeyValue as KeyValue
from django.test.client import RequestFactory
from api_v2.keyvalue_handler import KeyValueHandler
import json

factory = RequestFactory()


class Rack:
    rack_name = None
    tree = None
    kv = None
    ru = None
    width = None
    systems = []
    ethernet_patch_panel_24 = []
    ethernet_patch_panel_48 = []
    def __init__(self, rack_name):
        self.systems = []
        self.rack_name = rack_name
        self.kv = Truth.objects.select_related('truth_key_value').get(name=self.rack_name)
        self.system_list = KeyValue.objects.select_related('system').filter(value__contains="truth:%s" % (self.rack_name))
        self.ethernet_patch_panel_24 = self._get_ethernet_patch_panels(self.kv, 'ethernet', 24)
        self.ethernet_patch_panel_48 = self._get_ethernet_patch_panels(self.kv, 'ethernet', 48)
        import pdb
        h = KeyValueHandler()
        for s in self.system_list:
            request = factory.get('/api/v2/keyvalue/?keystore=%s' % (s.system.hostname), follow=True)
            tree = h.read(request)
            system_ru = self._get_system_ru(tree)
            system_image = self._get_system_image(tree)
            system_slot = self._get_system_slot(tree)
            self.systems.append({
                "system_name":s.system.hostname,
                "system_id":s.system.id,
                "system_ru":system_ru,
                "system_image":system_image,
                'system_slot':system_slot,
                'operating_system':str(s.system.operating_system), 
                'server_model': str(s.system.server_model),
                'oob_ip': str(s.system.oob_ip),
                })
            self.systems = sorted(self.systems, key=lambda k: k['system_slot']) 
        try:
            self.ru = self.kv.keyvalue_set.get(key='rack_ru').value
        except:
            self.ru = 42

        try:
            self.width = self.kv.keyvalue_set.get(key='rack_width').value
        except:
            self.width = 30
    def _get_ethernet_patch_panels(self, tree, type, port_count):
        ret = []
        for i in tree.keyvalue_set.all():
            match_string = "%i_port_%s_patch_panel" % (port_count, type)
            if str(i.key) == match_string:
                ret.append(i.value)
        return ret


    def _get_system_ru(self, tree):
        for i in tree.iterkeys():
            try:
                if 'system_ru' in i.split(':'):
                    return tree[i]
            except:
                pass
        return 4

    def _get_system_image(self, tree):
        for i in tree.iterkeys():
            try:
                if 'system_image' in i.split(':'):
                    return tree[i]
            except:
                pass
        return None

    def _get_system_slot(self, tree):
        for i in tree.iterkeys():
            try:
                if 'system_slot' in i.split(':'):
                    return tree[i]
            except:
                pass
        return 1
