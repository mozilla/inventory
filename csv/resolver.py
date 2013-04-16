# Reference for relationships and fields:
# http://people.mozilla.com/~juber/public/inventory.png

from systems.models import *
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist


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

    system_kv_patterns = []
    for key_type in ('mac_address', 'ip_address', 'name'):
        system_kv_patterns.append('nic.\d+.{0}.\d+'.format(key_type))
        system_kv_patterns.append('mgmt.\d+.{0}.\d+'.format(key_type))

    @system_kv
    def all_system_keyvalue(self, **kwargs):
        patterns = []
        for key_pattern in self.system_kv_patterns:
            patterns.append(re.compile(key_pattern))
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
    def license(self, **kwargs):
        name = 'license'
        values = ['license']
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
    def switch_ports(self, **kwargs):
        name = 'switch_ports'
        values = ['switch_ports']
        return self.generic_char(name, values, **kwargs)

    @system_attr
    def patch_panel_port(self, **kwargs):
        name = 'patch_panel_port'
        values = ['patch_panel_port']
        return self.generic_char(name, values, **kwargs)

    @system_attr
    def purchase_price(self, **kwargs):
        name = 'purchase_price'
        values = ['purchase_price']
        return self.generic_char(name, values, **kwargs)

    @system_attr
    def ram(self, **kwargs):
        name = 'ram'
        values = ['ram']
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

    def cannot_find(self, field):
        raise Exception(
            "Unfortunatly, we could not determine a {0} to use given the "
            "value {0}. Use the primary key of the {0} for better "
            "results.".format(field)
        )

    def get_related_simple(self, field, value, Klass):
        search = {field: value}
        obj = self._get_dict_related(search, Klass)
        if obj:
            return obj
        obj = self._get_pk_related(value, Klass)
        if obj:
            return obj
        self.cannot_find(field)

    def get_related(self, field, value, Klass, delimiter='%'):
        """
        Try to find delimited headers, fall back to normal get_realted_simple
        if they don't exist.
        """
        fields = field.split('%')
        if '%' not in field or len(fields) < 1:
            raise Exception(
                "We need to determine what fields to search for when looking "
                "for objects coresponding to the {0} header. Please specify "
                "them by doing something like: {0}%<field_name> ".format(field)
            )
        fields = field.split('%')[1:]
        values = value.split('%')
        search = dict(zip(fields, values))

        obj = self._get_dict_related(search, Klass)
        if obj:
            return obj
        self.cannot_find(field)

    def _get_dict_related(self, search, Klass):
        try:
            return Klass.objects.get(**search)
        except MultipleObjectsReturned:
            pass

    def _get_pk_related(self, value, Klass):
        try:
            return Klass.objects.get(pk=value)
        except ObjectDoesNotExist:
            pass

    @system_related
    def systemrack(self, **kwargs):
        def _systemrack(s, header, value):
            s.system_rack = self.get_related(header, value, SystemRack)
            return s
        bundle = {
            'name': 'systemrack',
            'values': ['system_rack'],
            'handler': _systemrack
        }
        return bundle

    @system_related
    def system_status(self, **kwargs):
        def _system_status(s, header, value):
            s.system_status = self.get_related(header, value, SystemStatus)
            return s
        bundle = {
            'name': 'systemstatus',
            'values': ['system_status'],
            'handler': _system_status
        }
        return bundle

    @system_related
    def server_model(self, **kwargs):
        def _server_model(s, header, value):
            s.system_model = self.get_related(header, value, ServerModel)
            return s
        bundle = {
            'name': 'server_model',
            'values': ['server_model'],
            'handler': _server_model
        }
        return bundle

    @system_related
    def operating_system(self, **kwargs):
        def _operating_system(s, header, value):
            sm = self.get_related(header, value, OperatingSystem)
            s.operating_system = sm
            return s
        bundle = {
            'name': 'operating_system',
            'values': ['operating_system'],
            'handler': _operating_system
        }
        return bundle

    @system_related
    def allocation(self, **kwargs):
        def _allocation(s, header, value):
            s.allocation = self.get_related(header, value, ServerModel)
            return s
        bundle = {
            'name': 'allocation',
            'values': ['allocation'],
            'handler': _allocation
        }
        return bundle

    @system_related
    def system_type(self, **kwargs):
        def _system_type(s, header, value):
            s.allocation = self.get_related(header, value, ServerModel)
            return s
        bundle = {
            'name': 'system_type',
            'values': ['system_type'],
            'handler': _system_type
        }
        return bundle
