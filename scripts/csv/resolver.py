
# Reference for relationships and fields:
# http://people.mozilla.com/~juber/public/inventory.png

test_csv = "/home/juber/inventory/inventory/scripts/csv"

from systems.models import *


class Generics(object):
    def generic_integer(self, name, values, default=None):
        def validate(s, value):
            if not value.isdigit():
                raise Exception(
                    "{0} {1} was not the right type".format(name, value)
                )
            setattr(s, name, value)
            return s
        bundle = {
            'name': name,
            'values': values,
            'handler': validate
        }
        return bundle

    def generic_char(self, name, values, default=None):
        bundle = {
            'name': name,
            'values': values,
            'handler': lambda s, c: setattr(s, name, c) or s
        }
        return bundle

    def generic_kevalue(self, re_patterns):
        """
        Validate a keyvalue header
        """
        def patterns_match(value):
            for pattern in re_patterns:
                if pattern.match(value):
                    return True
            return False

        def create_kv(s, key, value):
            import pdb;pdb.set_trace()
            return KeyValue.objects.get_or_create(
                system=s, key=key, value=value
            )[0]

        bundle = {
            'name': 'key_value',
            'match_func': patterns_match,
            'handler': create_kv
        }
        return bundle


class Resolver(Generics):
    def make_tagger(tagged_methods):
        def tag(func):
            tagged_methods[func.__name__] = func
            return func
        return tag

    system_attrs = {}
    system_attr = make_tagger(system_attrs)

    system_relateds = {}
    system_related = make_tagger(system_relateds)

    system_kvs = {}
    system_kv = make_tagger(system_kvs)

    @system_kv
    def all_system_keyvalue(self, **kwargs):
        patterns = []
        for key_type in ('mac_address', 'ip_address', 'name'):
            patterns.append(re.compile('nic.\d+.{0}.\d+'.format(key_type)))
            patterns.append(re.compile('mgmt.\d+.{0}.\d+'.format(key_type)))
        return self.generic_kevalue(patterns)

    @system_attr
    def rack_order(self, **kwargs):
        name = 'rack_order'
        values = ['rack_order']
        return self.generic_integer(name, values, **kwargs)

    @system_attr
    def notes(self, **kwargs):
        name = 'notes'
        values = ['notes']
        return self.generic_char(name, values, **kwargs)

    @system_attr
    def asset_tag(self, **kwargs):
        name = 'asset_tag'
        values = ['asset_tag']
        return self.generic_char(name, values, **kwargs)

    @system_attr
    def serial(self, **kwargs):
        name = 'serial'
        values = ['serial']
        return self.generic_char(name, values, **kwargs)

    @system_attr
    def switch_port(self, **kwargs):
        name = 'switch_port'
        values = ['switch_ports']
        return self.generic_char(name, values, **kwargs)

    @system_attr
    def oob_switch_port(self, **kwargs):
        name = 'oob_switch_port'
        values = ['oob_switch_&_port', 'oob_switch_ports']
        return self.generic_char(name, values, **kwargs)

    @system_attr
    def oob_ip(self, **kwargs):
        name = 'oob_ip'
        values = ['oob_ip']
        return self.generic_char(name, values, **kwargs)

    @system_attr
    def hostname(self, **kwargs):
        name = 'hostname'
        values = ['host_name', 'hostname']
        return self.generic_char(name, values, **kwargs)

    @system_related
    def systemrack(self, **kwargs):
        def _systemrack(s, value):
            r = SystemRack.objects.get(name=value)
            s.system_rack = r
            return s
        bundle = {
            'name': 'systemrack',
            'values': ['system_rack'],
            'handler': _systemrack
        }
        return bundle

    @system_related
    def system_status(self, **kwargs):
        def _system_status(s, value):
            status = SystemStatus.objects.get(status=value)
            s.system_status = status
            return s
        bundle = {
            'name': 'systemstatus',
            'values': ['system_status'],
            'handler': _system_status
        }
        return bundle
