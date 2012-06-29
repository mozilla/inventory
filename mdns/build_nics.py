import re
import pdb
import systems.models
from systems.models import System
from mdns.utils import *

import pprint
pp = pprint.PrettyPrinter(indent=2)

nic_nums = re.compile("^nic\.(\d+)\..*\.(\d+)$")
class Interface(object):
    mac = None
    hostname = None
    system = None
    nic_ = None

    def __init__(self, system, sub_nic):
        self.system = system
        self._nic = sub_nic # Just in case we need it for something
        tmp = nic_nums.match(sub_nic[0].key)
        if tmp:
            self.primary = tmp.group(1)
            self.alias = tmp.group(2)
        else:
            self.primary = None
            self.alias = None
        self.ips = []
        self.dns_auto_build = True
        self.dns_auto_hostname = True

    def has_dns_info(self):
        # Eventually do validation here
        if (isinstance(self.ips, type([])) and len(self.ips) > 0 and
                isinstance(self.hostname, basestring)):
            return True
        else:
            return False

    def set_kv(self, key, value):
        key_str = "nic.{0}.{1}.{2}".format(self.primary, key, self.alias)
        kv = self.system.keyvalue_set.filter(key=key_str)
        if kv:
            kv = kv[0]
            kv.value = value
            kv.save()
        else:
            kv = system.models.KeyValue(key=key_str, value=str(value))
            kv.save()

        setattr(self, key, value)
        return

    def pprint(self):
        pp.pformat(vars(self))

    def __str__(self):
        return "nic.{0}.{1} IP: {2} Hostname: {3}".format(self.primary,
                self.alias, self.ips, self.hostname)
    def __repr__(self):
        return "<Interface: {0}>".format(self)

is_mac_key = re.compile("^nic\.\d+\.mac_address\.\d+$")
is_hostname_key = re.compile("^nic\.\d+\.hostname\.\d+$")
is_ip_key = re.compile("^nic\.\d+\.ipv4_address\.\d+$")
is_dns_auto_build_key = re.compile("^nic\.\d+\.dns_auto_build\.\d+$")
is_dns_auto_hostname_key = re.compile("^nic\.\d+\.dns_auto_hostname\.\d+$")
is_dns_has_conflict_key = re.compile("^nic\.\d+\.dns_has_conflict\.\d+$")
is_some_key = re.compile("^nic\.\d+\.(.*)\.\d+$")

def build_nic(sub_nic):
    intr = Interface(sub_nic[0].system, sub_nic)
    for nic_data in sub_nic:
        if is_mac_key.match(nic_data.key):
            if intr.mac is not None:
                log("!" * 20, WARNING)
                log("nic with more than one mac in system "
                        "{0} (https://inventory.mozilla.org/en-US/systems/edit/{1}/)"
                        .format(intr.system, intr.system.pk), WARNING)
                log(pp.pformat(sub_nic), WARNING)
            intr.mac = nic_data.value
            continue
        if is_hostname_key.match(nic_data.key):
            if intr.hostname is not None:
                log("!" * 20, WARNING)
                log("nic with more than one hostname in system "
                        "{0} (https://inventory.mozilla.org/en-US/systems/edit/{1}/)"
                        .format(intr.system, intr.system.pk), WARNING)
                log(pp.pformat(sub_nic), WARNING)
            intr.hostname = nic_data.value
            continue
        if is_ip_key.match(nic_data.key):
            intr.ips.append(nic_data.value)
            continue
        if is_dns_auto_build_key.match(nic_data.key):
            if nic_data.value == 'False':
                intr.dns_auto_build = False
            continue
        if is_dns_auto_hostname_key.match(nic_data.key):
            if nic_data.value == 'False':
                intr.dns_auto_hostname = False
            continue
        if is_dns_has_conflict_key.match(nic_data.key):
            if nic_data.value == 'True':
                intr.dns_has_conflict = True
            else:
                intr.dns_has_conflict = False
            continue
        tmp = is_some_key.match(nic_data.key)
        if tmp:
            if hasattr(intr, tmp.group(1)):
                setattr(intr, tmp.group(1), [nic_data.value,
                    getattr(intr, tmp.group(1))])

            else:
                setattr(intr, tmp.group(1), nic_data.value)
    if intr.hostname is None:
        log("System {0} and nic {1}/{2} hast no hostname key, using hostname "
            "found on the system.".format(print_system(intr.system), intr.primary,
            intr.alias), ERROR)
        intr.hostname = intr.system.hostname

    return intr

def get_nic_objs():
    """
    Use this function to return all data that *could* be included in a DNS
    build.
    :return: list of tuples. See :function:`get_nick_data`
    """
    systems = System.objects.all()
    formated_nics = []
    for system in systems:
        raw_nics = system.keyvalue_set.all()
        if not raw_nics:
            continue
        formated_nics.append(transform_nics(raw_nics))

    interfaces = []
    for system_nics in formated_nics:
        for primary_nic_number, primary_nic in system_nics.items():
            for sub_nic_number, sub_nic in primary_nic['sub_nics'].items():
                interface = build_nic(sub_nic)
                if not interface:
                    continue
                interfaces.append(interface)
    return interfaces


def get_dns_data():
    dns_data, nic_objs = _get_dns_data()
    return dns_data


get_nic_primary_number = re.compile("^nic\.(\d+).*$")


def transform_nics(nics):
    """
    Since KV systems have no structure, storing structured data in a KV makes
    extracting data very hard. This function applies a transform to all nics
    linked to a system. It builds a structure that contains all nics in a
    useful format.

    The transform should return something like this::

        {'0': {'sub_nics': {'0': ['nic.0.ipv4_address.0': '192.168.1.1',
                                  'nic.0.mac_address.0': 'DE:AD:BE:EF:00:00'
                                  'nic.0.hostname.0': 'foobar']
                            '1': ['nic.0.ipv4_address.1': '192.168.1.1',
                                  'nic.0.mac_address.1': 'DE:AD:BE:EF:00:00'
                                  'nic.0.hostname.1': 'foobar']}}
         '1': {'sub_nics': {'0': ['nic.1.ipv4_address.0': '192.168.1.1',
                                  'nic.1.mac_address.0': 'DE:AD:BE:EF:00:00'
                                  'nic.1.hostname.0': 'foobar']
                            '1': ['nic.1.ipv4_address.1': '192.168.1.2',
                                  'nic.1.mac_address.1': '11:22:33:44:55:66'
                                  'nic.1.hostname.1': 'bazbar']}}}
    """
    formated_nics = _build_primary_nics(nics)
    for nic_number, nics in formated_nics.items():
        formated_nics[nic_number]['sub_nics'] = _build_sub_nics(nics)
        formated_nics[nic_number].pop('nics')  # We don't need nics anymore.

    return formated_nics


def _build_primary_nics(all_nics):
    """
    Aggregate all nics into their primary groups.
    I.E. All nic\.X.\.*\.Y nics go into a list where all X's are the same.

    :param all_nics: All nics to consider.
    :type all_nics: list
    """
    primary_nics = {}
    for nic in all_nics:
        if not isinstance(nic.key, basestring):
            log("=" * 15, DEBUG)
            log("System {0} and NIC {1} not in valid format.  Value is not "
                    "type basestring Skipping.".format(nic.system, nic), DEBUG)
            log(print_system(nic.system), DEBUG)
            continue
        possible_primary_nic = get_nic_primary_number.match(nic.key)
        if not possible_primary_nic:
            log("=" * 15, DEBUG)
            log("System {0} and NIC {1} not in valid format. "
                "Skipping.".format(nic.system, nic), DEBUG)
            log(print_system(nic.system), DEBUG)
            continue
        primary_nic_number = possible_primary_nic.group(1)
        if primary_nic_number in primary_nics:
            primary_nics[primary_nic_number]['nics'].append(nic)
        else:
            primary_nics[primary_nic_number] = {'nics': [nic]}
    return primary_nics


get_nic_sub_number = re.compile("^nic\.\d+.*\.(\d+)$")


def _build_sub_nics(all_nics):
    """
    Aggregate all sub nics into their sub groups.
    I.E. All nic\.X.\.*\.Y nics go into a list where all Y's are the same.

    :param all_nics: All nics to consider.
    :type all_nics: list
    """
    sub_nics = {}
    for nic in all_nics['nics']:
        possible_sub_nic = get_nic_sub_number.match(nic.key)
        if not possible_sub_nic:
            log("System {0} and NIC {1} not in valid format. "
                "Skipping.".format(nic.system, nic.key), DEBUG)
            continue
        sub_nic_number = possible_sub_nic.group(1)
        if sub_nic_number in sub_nics:
            sub_nics[sub_nic_number].append(nic)
        else:
            sub_nics[sub_nic_number] = [nic]
    return sub_nics
