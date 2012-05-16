from truth.models import Truth
from systems.models import System
from dns.build_nics import *

import ipaddr

import re
import copy
import pprint
import pdb

pp = pprint.PrettyPrinter(indent=2)


def get_dns_data():
    """
    Use this function to return all data that *could* be included in a DNS
    build.
    :return: list of tuples. See :function:`get_ip_mac_hostname`
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
                info = get_ip_mac_hostname(sub_nics)
                if not info:
                    continue
                dns_data.append(info)
    return dns_data


def aggrigate_sites():
    dns_data = get_dns_data()

def do_dns_build():
    build_sites([
                ('10.22.74.0/24', 'dmz.scl3')
            ])

def build_sites(sites):
    """
    For each site in sites build DNS zone (reverse and forward) files.
    Sites have the form::

        ('<vlan-name>.<site-name>', <'network-mask'>)

    For example::

        ('dmz.scl3', '10.22.74.0/24')
    """
    aggrigated_sites = {}
    for site in sites:
        # Precalculate the regest patterns so we can do this in one pass.
        name, network = site
        # Add address family logic here if need be.
        try:
            aggrigated_sites[name] = (ipaddr.IPv4Network(network), [])
        except ipaddr.AddressValueError, e:
            # Eventually send an email or do something more serious about an error here.
            print str(e)

    def sanity_check(hostnames):
        if len(hostnames) == 1:
            return True
        if hostnames[0] != hostnames[1]:
            return True
        else:
            return sanity_check(hostnames[1:])

    for host in get_dns_data():
        # BAH! this isn't a FQDN (hostname), it's more likely a single or multiple labels.
        ips, macs, hostname, nic = host
        # Sanity check. All the hostnames should be the same.
        if not sanity_check(hostname):
            print "ERROR: Sanity check failed on nic {0}".format(nic)
            continue

        for name, data in aggrigated_sites.items():
            network, entries = site_data
            for ip in ips:
                if ipaddr.IPv4Network(ip).overlaps(network):
                    entries.append(host)

    pp.pprint(aggrigated_sites)
