# Reference for relationships and fields:
# http://people.mozilla.com/~juber/public/inventory.png

from django.core.exceptions import (
    MultipleObjectsReturned, ValidationError, FieldError
)
from systems import models as sys_models

import datetime
import re


class Generics(object):
    def generic_integer(self, name, values, default=None):
        def validate(s, value):
            if not value.isdigit():
                raise ValidationError(
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

    def generic_float(self, name, values, default=None):
        def validate(s, value):
            try:
                value = str(float(value))
            except ValueError:
                raise ValidationError(
                    "{0} {1} coult not be coerced into a float".format(
                        name, value)
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
            return sys_models.KeyValue.objects.get_or_create(
                obj=s, key=key, value=value
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
    metas = {}
    meta = make_tagger(metas)

    system_attrs = {}
    system_attr = make_tagger(system_attrs)

    system_relateds = {}
    system_related = make_tagger(system_relateds)

    system_kvs = {}
    system_kv = make_tagger(system_kvs)

    system_kv_patterns = []
    for key_type in (
        'mac_address', 'ip_address', 'name', 'hostname', 'dhcp_scope',
        'option_hostname', 'dhcp_filename', 'dhcp_domain_name',
        'dhcp_domain_name_servers'
    ):
        system_kv_patterns.append('nic.\d+.{0}.\d+'.format(key_type))
        system_kv_patterns.append('mgmt.\d+.{0}.\d+'.format(key_type))
    system_kv_patterns.append('system.hostname.alias.\d+')

    @meta
    def primary_attribute(self, **kwargs):
        def _primary_attribute(s, header, value, **kwargs):
            try:
                _, s._primary_attr = map(
                    lambda s: s.strip(), header.split('%')
                )
            except ValueError:
                raise ValidationError(
                    "The primary_attribute header must be in the form "
                    "'primary_attribute%<system-attribute-header>'"
                )
            s._primary_value = getattr(
                self.get_related(header, value, sys_models.System),
                s._primary_attr
            )
            return s

        bundle = {
            'name': 'primary_attribute',
            'filter_fields': ['asset_tag', 'hostname'],
            'values': ['primary_attribute'],
            'handler': _primary_attribute,
        }
        return bundle

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
        return self.generic_float(name, values, **kwargs)

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

    @system_attr
    def purchase_date(self, **kwargs):
        name = 'purchase_date'
        values = ['purchase_date']
        return self.generic_char(name, values, **kwargs)

    def gen_parse_date(self, field):
        def parse_date(s, value, **kwargs):
            d = datetime.datetime.strptime(value, "%Y-%m-%d").date()
            setattr(s, field, d)
            return s
        return parse_date

    @system_attr
    def warranty_start(self, **kwargs):
        name = 'warranty_start'
        values = ['warranty_start']
        bundle = self.generic_char(name, values, **kwargs)
        bundle['handler'] = self.gen_parse_date(name)
        return bundle

    @system_attr
    def warranty_end(self, **kwargs):
        name = 'warranty_end'
        values = ['warranty_end']
        bundle = self.generic_char(name, values, **kwargs)
        bundle['handler'] = self.gen_parse_date(name)
        return bundle

    def cannot_find(self, field, value):
        raise ValidationError(
            "Unfortunatly, we could not determine a {0} to use given the "
            "value '{1}'".format(field, value)
        )

    def get_related_simple(self, field, value, Klass):
        search = {field: value}
        obj = self.get_realted_from_dict(search, Klass)
        if obj:
            return obj
        obj = self.get_related_from_pk(value, Klass)
        if obj:
            return obj
        self.cannot_find(field, value)

    def get_related(self, field, value, Klass, delimiter='%'):
        """
        Try to find delimited headers, fall back to normal get_realted_simple
        if they don't exist.
        """
        fields = map(lambda s: s.strip(), field.split('%'))
        if '%' not in field or len(fields) < 1:
            raise ValidationError(
                "We need to determine what fields to search for when looking "
                "for objects coresponding to the {0} header. Please specify "
                "some filter fields by doing something like: "
                "{0}%({1})'".format(
                    field, ' | '.join(self.get_field_names(Klass))
                )
            )
        fields = fields[1:]
        values = map(lambda s: s.strip(), value.split('%'))
        search = dict(zip(fields, values))

        try:
            obj = self.get_realted_from_dict(search, Klass)
        except FieldError, e:
            raise Exception(
                "When trying to use resolve a(n) {0}, got the error "
                "{1}".format(Klass.__name__, str(e))
            )
        if obj:
            return obj
        self.cannot_find(field, value)

    def get_realted_from_dict(self, search, Klass):
        try:
            return Klass.objects.get(**search)
        except (MultipleObjectsReturned, Klass.DoesNotExist):
            pass

    def get_related_from_pk(self, value, Klass):
        try:
            return Klass.objects.get(pk=value)
        except Klass.DoesNotExist:
            pass

    # XXX this should really be in the classes themselves
    def get_field_names(self, Klass):
        return [field.name for field in Klass._meta.fields]

    @system_related
    def systemrack(self, **kwargs):
        def _systemrack(s, header, value):
            s.system_rack = self.get_related(
                header, value, sys_models.SystemRack
            )
            return s

        filter_fields = self.get_field_names(sys_models.SystemRack)
        filter_fields[filter_fields.index('location')] = 'location__name'

        bundle = {
            'name': 'systemrack',
            'filter_fields': filter_fields,
            'values': ['system_rack'],
            'handler': _systemrack
        }
        return bundle

    @system_related
    def system_status(self, **kwargs):
        def _system_status(s, header, value):
            s.system_status = self.get_related(
                header, value, sys_models.SystemStatus
            )
            return s
        bundle = {
            'name': 'systemstatus',
            'filter_fields': self.get_field_names(sys_models.SystemStatus),
            'values': ['system_status'],
            'handler': _system_status
        }
        return bundle

    @system_related
    def server_model(self, **kwargs):
        def _server_model(s, header, value):
            s.server_model = self.get_related(
                header, value, sys_models.ServerModel
            )
            return s
        bundle = {
            'name': 'server_model',
            'filter_fields': self.get_field_names(sys_models.ServerModel),
            'values': ['server_model'],
            'handler': _server_model
        }
        return bundle

    @system_related
    def operating_system(self, **kwargs):
        def _operating_system(s, header, value):
            sm = self.get_related(header, value, sys_models.OperatingSystem)
            s.operating_system = sm
            return s
        bundle = {
            'name': 'operating_system',
            'filter_fields': self.get_field_names(sys_models.OperatingSystem),
            'values': ['operating_system'],
            'handler': _operating_system
        }
        return bundle

    @system_related
    def allocation(self, **kwargs):
        def _allocation(s, header, value):
            s.allocation = self.get_related(
                header, value, sys_models.Allocation
            )
            return s
        bundle = {
            'name': 'allocation',
            'filter_fields': self.get_field_names(sys_models.Allocation),
            'values': ['allocation'],
            'handler': _allocation
        }
        return bundle

    @system_related
    def system_type(self, **kwargs):
        def _system_type(s, header, value):
            s.system_type = self.get_related(
                header, value, sys_models.SystemType
            )
            return s
        bundle = {
            'name': 'system_type',
            'filter_fields': self.get_field_names(sys_models.SystemType),
            'values': ['system_type'],
            'handler': _system_type
        }
        return bundle
