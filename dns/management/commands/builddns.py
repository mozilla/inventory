from django.core.management.base import BaseCommand, CommandError

from systems.models import KeyValue, System

import re
import copy
import pprint
import pdb

pp = pprint.PrettyPrinter(indent=4)

class Command(BaseCommand):
    args = ''
    help = 'Build dns files'

    def handle(self, *args, **options):
        build()

def build():
    systems = System.objects.all()
    nics = []
    for system in systems:
        raw_nics = system.keyvalue_set.all()
        if not raw_nics:
            continue
        nics.append((system, _transform_nics(raw_nics)))
    pp.pprint(nics)
    return
    nic_data = get_ip_mac_hostname(nics)
    for data in nic_data:
        ip, mac, hostname, nic = data
        print "In System {0}: ip: {1} mac: {2} hostname: {3}".format(ip,
                mac, hostname)

is_mac_key = re.compile("^nic\.\d+\.mac_address\.\d+$")
def get_ip_mac_hostname(nics):
    """
    Gather information about all nics of a system.

    .. note::
        This function assumes that all data in the database is valid *and*
        sanitized (in valid ip/mac/hostname format).

    :returns: Return a list of tuples containing (ip, mac, hostname, nic). nic
        is the object that originally contained the other info. It is used if we
        need to backtrack for more info (temporary).

    """
    for nic in nics:
        if is_mac_key.match(nic.value):
            mac = nic.value
            continue


get_nic_primary_number = re.compile("^nic\.(\d+).*$")

def _transform_nics(nics):
    """
    Since KV systems have no structure, storing data that has structure in them
    makes extracting data very hard. This function applies a format structure
    to all fo the nics. Fighting hacks with hacks.
    """
    formated_nics = _build_primary_nics(nics)
    for nic_number, nics in formated_nics.items():
        formated_nics[nic_number]['sub_nics'] = _build_sub_nics(nics)
    return formated_nics



def _build_primary_nics(nics):
    primary_nics = {}
    tmp_nics = copy.deepcopy(nics)
    for nic in nics:
        if not isinstance(nic.key, basestring):
            print("System {0} and NIC {1} not in valid format. "
                "Value is not type basestring Skipping.".format(nic.system, nic))
            continue
        possible_primary_nic = get_nic_primary_number.match(nic.key)
        if not possible_primary_nic:
            print("System {0} and NIC {1} not in valid format. "
                "Skipping.".format(nic.system, nic))
            continue
        primary_nic_number = possible_primary_nic.group(1)
        if primary_nics.has_key(primary_nic_number):
            primary_nics[primary_nic_number]['nics'].append(nic)
        else:
            primary_nics[primary_nic_number] = {'nics': [nic]}
    return primary_nics



get_nic_sub_number = re.compile("^nic\.\d+.*\.(\d+)$")

def _build_sub_nics(all_nics):
    """
    :param nic_number: Primary nic number
    :type nic_number: str
    :param nics: All nics of primary nic
    :type nic_number: list
    """
    sub_nics = {}
    for nic in all_nics['nics']:
        possible_sub_nic = get_nic_sub_number.match(nic.key)
        if not possible_sub_nic:
            print("System {0} and NIC {1} not in valid format. "
                "Skipping.".format(nic.system, nic.key))
            continue
        sub_nic_number = possible_sub_nic.group(1)
        if sub_nics.has_key(sub_nic_number):
            sub_nics[sub_nic_number].append(nic)
        else:
            sub_nics[sub_nic_number] = [nic]
    return sub_nics
