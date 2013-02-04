#!/usr/bin/python

from django.core.management import setup_environ
import settings
setup_environ(settings)

from systems.models import System, KeyValue
from truth.models import Truth, KeyValue as TruthKeyValue
import re
from MacroExpansion import MacroExpansion
class KeyValueTree:
    def __init__(self,search_string):
        self.ret = []
        self.final = {}
        self.is_system = False
        self.is_truth = False
        self.search_string = search_string
        base = None
        truth_only = False
        host_only = False
        if re.match("host:.*", search_string):
            host_only = True
            search_string = search_string.split(":")[1]
        if re.match("truth:.*", search_string):
            truth_only = True
            search_string = search_string.split(":")[1]
        if truth_only is False:
            try:
                system = System.objects.get(hostname=search_string)
                base = KeyValue.expanded_objects.filter(system=system)
                self.is_system = True
            except:
                self.is_system = False
                base = None
        if base is None and host_only is False:
            try:
                truth = Truth.objects.get(name=search_string)
                base = TruthKeyValue.expanded_objects.filter(truth=truth)
                self.is_truth = True
            except:
                self.is_truth = False
                return None
        tmp_list = []
        #Let's start at our child node, first getting out own keys, these will not get overwritten by those of our parents
        for row in base: 
            matches = re.match("\$\{(.*)\}", row.value) 
            if not re.search("parent", row.key): 
                if matches is not None: 
                    m = MacroExpansion(matches.group(1)) 
                    row.value = m.output() 
        ##Now we've got our base keys, lets get those of our parents
        for row in base:

            matches = re.match("(parent.*)", row.key)
            if matches is not None:
                parent_type = row.value.replace("${","").split(':')[0]
                parent_name = row.value.replace("}","").split(':')[1]
                tmp = self.get_parents(parent_type, parent_name, root=True)
                #Ok now i've got my own parents
                for host in tmp:
                    #tmp = {'key':host['key'], 'value':host['value']}
                    tmp_list.append(host)

        #build a list of all of the parents keys as dictionary objects
        for row in tmp_list:
            if 'key' in row and 'value' in row:
                self.final[row['key']] = row['value']

        #overwrite the parents kv/store with my own
        for row in base:
            self.final[row.key] = row.value

    def get_parents(self, parent_type, parent_name, root=False):
        #ret = []
        if parent_type is not None and parent_name is not None:
            obj = None
            if parent_type == 'host':
                obj = System.objects.get(hostname=parent_name)
                base = KeyValue.expanded_objects.filter(system=obj).exclude(key__contains='parent')
                base_parents = KeyValue.expanded_objects.filter(system=obj,key__contains='parent')
                parent_compare = obj.hostname
            elif parent_type == 'truth':
                obj = Truth.objects.get(name=parent_name)
                base = TruthKeyValue.expanded_objects.filter(truth=obj).exclude(key__contains='parent')
                base_parents = TruthKeyValue.expanded_objects.filter(truth=obj,key__contains='parent')
                parent_compare = obj.name


            if base is not None and obj is not None:
                for host in base:
                    if host.value is not None and host.key is not None:
                        matches = re.match("\$\{(.*)\}", host.value) 
                        if not re.search("parent", host.key): 
                            if matches is not None: 
                                m = MacroExpansion(matches.group(1))
                                host.value = m.output()
                    if host.key is not None and host.value is not None:
                        if self.search_string != parent_compare:
                            host.key = "%s:%s:%s" % (parent_type, parent_name, host.key)
                        tmp = {'key':host.key, 'value':host.value}
                        self.ret.append(tmp)
                for row in base_parents:
                    parent_type = row.value.replace("${","").split(':')[0]
                    parent_name = row.value.replace("}","").split(':')[1]
                    self.ret.append(self.get_parents(parent_type, parent_name, root=False))


                """for host in base:
                    if host.value is not None and host.key is not None:
                        matches = re.match("\$\{(.*)\}", host.value) 
                        if not re.search("parent", host.key): 
                            if matches is not None: 
                                m = MacroExpansion(matches.group(1))
                                host.value = m.output()
                    if host.key is not None and host.value is not None:
                        #Not sure if i'll keep this or not, but display the parent's name in ()
                        if self.search_string != truth.hostname:
                            host.key = "truth:%s:%s" % (parent_name, host.key)
                        tmp = {'key':host.key, 'value':host.value}
                        self.ret.append(tmp)

                base_parents = TruthKeyValue.expanded_objects.filter(truth=truth,key__contains='parent')
                for row in base_parents:
                    parent_type = row.value.replace("${","").split(':')[0]
                    parent_name = row.value.replace("}","").split(':')[1]
                    self.ret.append(self.get_parents(parent_type, parent_name, root=False))"""

            return self.ret        
        else:
            return None
