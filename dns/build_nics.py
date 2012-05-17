import re
import pdb
from systems.models import System


def get_dns_data():
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
    dns_data = []
    for system_nics in formated_nics:
        for primary_nic_number, primary_nic in system_nics.items():
            for sub_nic_number, sub_nics in primary_nic['sub_nics'].items():
                info = get_nick_data(sub_nics)
                if not info:
                    continue
                dns_data.append(info)
    return dns_data

is_mac_key = re.compile("^nic\.\d+\.mac_address\.\d+$")
is_hostname_key = re.compile("^nic\.\d+\.hostname\.\d+$")
is_ip_key = re.compile("^nic\.\d+\.ipv4_address\.\d+$")
is_dns_auto_build_key = re.compile("^nic\.\d+\.dns_auto_build\.\d+$")
is_dns_auto_hostname_key = re.compile("^nic\.\d+\.dns_auto_hostname\.\d+$")


def get_nick_data(sub_nics):
    """
    Gather information about all nics of a system.

    .. note::
        This function assumes that all data in the database is valid *and*
        sanitized (in valid ip/mac/hostname format).

    :return: Return a list of tuples containing (ip, mac, hostname, nic). nic
    is the object that originally contained the other info. It is used if we
    need to backtrack for more info (like getting the system).
    """
    #TODO return the nic in the tuple.
    data = {}
    for nic in sub_nics:
        if is_mac_key.match(nic.key):
            data.setdefault('macs', []).append(nic.value)
            continue
        if is_hostname_key.match(nic.key):
            data.setdefault('hostname', []).append(nic.value)
            continue
        if is_ip_key.match(nic.key):
            data.setdefault('ip', []).append(nic.value)
            continue
        if is_dns_auto_build_key.match(nic.key):
            data.setdefault('dns_build_options',
                    {})['dns_auto_build'] = nic.value
            continue
        if is_dns_auto_hostname_key.match(nic.key):
            data.setdefault('dns_build_options',
                    {})['dns_auto_hostname'] = nic.value
            continue

    if not('macs' in data and 'hostname' in data and
            'ip' in data):
        return None
    data['nic'] = nic
    return (data['ip'], data['macs'], data['hostname'], data)


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
            # TODO, should something more useful happen with this alert? Write
            # to a log file?
            print("System {0} and NIC {1} not in valid format.  Value is not "
                    "type basestring Skipping.".format(nic.system, nic))
            continue
        possible_primary_nic = get_nic_primary_number.match(nic.key)
        if not possible_primary_nic:
            print("System {0} and NIC {1} not in valid format. "
                "Skipping.".format(nic.system, nic))
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
            print("System {0} and NIC {1} not in valid format. "
                "Skipping.".format(nic.system, nic.key))
            continue
        sub_nic_number = possible_sub_nic.group(1)
        if sub_nic_number in sub_nics:
            sub_nics[sub_nic_number].append(nic)
        else:
            sub_nics[sub_nic_number] = [nic]
    return sub_nics
