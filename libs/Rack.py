# To test this: ./manage.py test -s libs/test_Rack.py



from KeyValueTree import KeyValueTree
from truth.models import KeyValue as TruthKeyValue, Truth
from systems.models import KeyValue as KeyValue
from django.test.client import Client
import json
class Rack:
    rack_name = None
    tree = None
    kv = None
    ru = None
    width = None
    systems = []
    def __init__(self, rack_name):
        self.systems = []
        self.rack_name = rack_name
        self.kv = Truth.objects.select_related('truth_key_value').get(name=self.rack_name)
        self.system_list = KeyValue.objects.select_related('system').filter(value__contains="truth:%s" % (self.rack_name))
        for s in self.system_list:
            #print dir(s)
            client = Client()
            resp = client.get('/api/v2/keyvalue/?keystore=%s' % (s.system.hostname), follow=True)
            tree = json.loads(resp.content) 
            system_ru = self._get_system_ru(tree)
            system_image = self._get_system_image(tree)
            system_slot = self._get_system_slot(tree)
            self.systems.append({"system_name":s.system.hostname, "system_ru":system_ru, "system_image":system_image, 'system_slot':system_slot})
            self.systems = sorted(self.systems, key=lambda k: k['system_slot']) 
        try:
            self.ru = self.kv.keyvalue_set.get(key='rack_ru').value
        except:
            self.ru = 42

        try:
            self.width = self.kv.keyvalue_set.get(key='rack_width').value
        except:
            self.width = 30
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
