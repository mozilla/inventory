from truth.models import Truth

from migrate_dns.build_nics import *
from migrate_dns.utils import *
import ipaddr
from systems.models import ScheduledTask
from core.interface.static_intr.models import StaticInterface

from mozdns.address_record.models import AddressRecord
from mozdns.ptr.models import PTR
from mozdns.domain.utils import *

import os.path
import pprint

DEBUG = 3
DO_DEBUG = False

pp = pprint.PrettyPrinter(indent=2)

def ip_to_site(ip_str, base_site_path):
    """Given the dotted decimal of an IP address, find the site it corresponds
    to. If no site is found return None. This function assumes that the ip is
    in valid format.

    :param ip_str: The ip to use.
    :type ip_str: str
    :param base_site_path: The dir containing all other sites (usually MOZ_SITE_PATH)
    :type base_site_path: str
    :returns key_value: The kv representing the site the ip belongs in.
    :type key_value: truth.models.KeyValue
    """
    print "IP string" + ip_str
    ip = ipaddr.IPv4Network(ip_str)  # This will end up being <ip>/32
    sites = get_all_sites(base_site_path)
    ip2v = Truth.objects.get(name='ip_to_vlan_mapping').keyvalue_set.all()
    for kv in ip2v:
        vlan_site, network_str = kv.key, kv.value
        if ipaddr.IPv4Network(network_str).overlaps(ip):
            return kv
    return None

def get_all_sites(site_path):
    """
    Return every site in the ip_to_vlan_mapping truth store.
    """
    sites = []
    ip2v = Truth.objects.get(name='ip_to_vlan_mapping').keyvalue_set.all()
    for kv in ip2v:
        vlan_site, network = kv.key, kv.value
        vlan, site = vlan_site.split('.')
        full_site_path = os.path.join(site_path, site)
        sites.append((vlan_site, network, full_site_path))
    return sites

def get_ui_sites_changed(all_sites):
    sites_to_build = []
    tasks = ScheduledTask.objects.filter(type='dns')
    for site_meta in all_sites:
        vlan_site, network, site_path = site_meta
        for t in tasks:
            if vlan_site == t.task:
                print vlan_site
                sites_to_build.append(site_meta)
                t.delete()

    return sites_to_build

def guess(nic):
    """
    Search and Guess which object in the database is supposed to correspond
    with this nic.
    """
    log("Attempting to find records for nic {0}".format(nic))
    if len(nic.ips) != 1:
        log("nic {0} system {1} doesn't have the right amount of ip's."
                .format(nic, print_system(nic.system)), ERROR)
        return None, None, None

    addrs = AddressRecord.objects.filter(ip_str=nic.ips[0])
    ptrs = PTR.objects.filter(ip_str=nic.ips[0])
    intrs = StaticInterface.objects.filter(ip_str=nic.ips[0])

    # This script probably put this info here.
    exintr = None
    for intr in intrs:
        if intr.fqdn.startswith(nic.hostname):
            log("Found Interface {0} that matches nic.ip {1} and partially "
                "nic.hostname {2}".format(intr, nic.ips[0], nic.hostname))
            if exintr:
                log("Found another Interface {0} that looks a lot like {1}, "
                    "while searching for nic.ip {2} and nic.hostname {3}."
                    "{2}".format(intr, exintr, nic.ips[0], nic.hostname),
                    WARNING)
            exintr = intr

    # Ok, we have records with the same ip. Look for name matches.
    exaddr = None
    for addr in addrs:
        if addr.fqdn.startswith(nic.hostname):
            # The ip patches and the hostname of the nic lines up with the
            # name on the Address Record.
            log("Found A {0} that matches nic.ip {1} and partially "
                "nic.hostname {2}".format(addr, nic.ips[0], nic.hostname))
            if exaddr:
                log("Found another A record {0} that looks a lot like {1}, "
                    "while searching for nic.ip {2} and nic.hostname {3}."
                    "{2}".format(addr, exaddr, nic.ips[0], nic.hostname),
                    WARNING)
            exaddr = addr

    # Search in the ptr space.
    exptr = None
    for ptr in ptrs:
        if ptr.name.startswith(nic.hostname):
            log("Found PTR {0} that matches nic.ip {1} and partially "
                "nic.hostname {2}".format(ptr, nic.ips[0],
                 nic.hostname))
            if exptr:
                log("Found another PTR record {0} that looks a lot like {1}, "
                    "while searching for nic.ip {2} and nic.hostname {3}."
                    "{2}".format(addr, exaddr, nic.ips[0], nic.hostname),
                    WARNING)
            exptr = ptr

    return exintr, exaddr, exptr

def populate_interface():
    matches = []
    misses = []
    for nic in get_nic_objs():
        log("="*20)
        intr, addr, ptr = guess(nic)
        if not (intr or addr or ptr):
            log("Epic failure. Couldn't find anything for nic.{0}.{1} "
                    "{2}".format(nic.primary, nic.alias,
                        print_system(nic.system)), ERROR)
            misses.append(nic)
        else:
            log("SUCCESS: Guess Interface:{0} AddressRecord:{1} PTR:{2}".format(intr, addr, ptr))
            matches.append((nic, intr, addr, ptr))

    log("-+"*80)
    log("===== Misses =====")
    for nic in misses:
        log(str(nic))
    log("===== Matches =====")
    for nic, intr, addr, ptr in matches:
        log("Nic: {1} Interface:{0} AddressRecord:{1} PTR:{2}".format(nic, intr, addr, ptr))
    log("Misses: " + str(len(misses)))
    log("Matches: " + str(len(matches)))
