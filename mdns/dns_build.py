from truth.models import Truth

from mdns.inventory_build import inventory_build_sites
from mdns.svn_build import collect_svn_zones, collect_rev_svn_zones
from mdns.svn_build import get_forward_svn_sites_changed
from mdns.svn_build import get_reverse_svn_sites_changed
from mdns.build_nics import *
from mdns.utils import *
import ipaddr
from systems.models import ScheduledTask
from settings import MOZ_SITE_PATH
from settings import REV_SITE_PATH
from settings import ZONE_PATH
from settings import RUN_SVN_STATS

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

def do_dns_build():
    # The function get_all_sites should generate tuples like:
    #   ('<site-name>', '<network>', '<file_path_to_site_dir>')

    all_sites = set(get_all_sites(MOZ_SITE_PATH))
    sites_to_build = set()

    changed_ui = set(get_ui_sites_changed(all_sites))
    sites_to_build = sites_to_build.union(changed_ui)

    changed_forward = set(get_forward_svn_sites_changed(all_sites,
        MOZ_SITE_PATH))
    sites_to_build = sites_to_build.union(changed_forward)

    changed_reverse = set(get_reverse_svn_sites_changed(all_sites,
        REV_SITE_PATH))
    sites_to_build = sites_to_build.union(changed_reverse)

    log("====== Sites to build", INFO)
    for vlan_site, network, site_path in sites_to_build:
        vlan, site = vlan_site.split('.')
        log("Building {0} for vlan {1} ({2}). Site is in {3}".format(site, vlan, network,
            site_path))

    if not sites_to_build:
        log("No sites to build.", INFO)
        log("Done.", INFO)
        return

    inv_forward, inv_reverse = inventory_build_sites(sites_to_build)
    if DO_DEBUG:
        log( "=" * 10 + "Forward sites" + "=" * 10 , DEBUG)
        for site, data in inv_forward.items():
            log("-" * 10 + site, DEBUG)
            network, entries = data
            for thing in entries:
                log(thing.pprint(), DEBUG)

        log("=" * 10 + "Reverse sites" + "=" * 10, DEBUG)
        for site, data in inv_reverse.items():
            site_path, intrs = data
            log("-" * 10 + site, DEBUG)
            log(site_path, DEBUG)
            for intr in intrs:
                intr.pprint()

    svn_zones = collect_svn_zones(MOZ_SITE_PATH, ZONE_PATH)
    rev_svn_zones = collect_rev_svn_zones(REV_SITE_PATH, ZONE_PATH)

    if RUN_SVN_STATS:
        # We have the data, let's do some analysis.
        analyse_svn(svn_zones, rev_svn_zones)

    build_forward(sites_to_build, inv_forward, svn_zones)
    # The reason why this is done in two different functions rather than one is
    # we might want to include PTR records that aren't part of a system. If we
    # do this we will need go and get those from the KV store. That can be done
    # in the build_reverse function.
    build_reverse(sites_to_build, inv_reverse, rev_svn_zones)

    log("Rebuilding Hashes (SOAs serials were changed).", INFO)
    # These two functions will update the hashes truth store with fresh hashes.
    get_forward_svn_sites_changed(all_sites, MOZ_SITE_PATH)
    get_reverse_svn_sites_changed(all_sites, REV_SITE_PATH)

    log("Done.", INFO)

def build_reverse(sites_to_build, inv_reverse, rev_svn_zones):
    final_records = {}
    for network, interfaces in inv_reverse.items():
        network_path, svn_entries = rev_svn_zones[network]
        network_path, inv_entries = final_records.setdefault(network,
                (network_path, set()))
        # TODO, rename inv_entries to something more descriptive.
        for intr in interfaces:
            name = intr.hostname + "."
            for ip in intr.ips:
                dnsip = ip2dns_form(ip)
                if (dnsip, name) in svn_entries:
                    log("System {0} (interface: {1}, {2}) has "
                        "conflict".format(intr.system, dnsip, name), INFO)
                else:
                    inv_entries.add((dnsip, name))

    log("=" * 10 + " Final DNS data", BUILD)
    for network, network_data in final_records.items():
        network_path, records = network_data
        # Inv entries are in (<'name'>, <'ip'>) form
        generate_reverse_inventory_data_file(network, records, network_path)


def build_forward(sites_to_build, inv_forward, svn_zones):

    final_records = {}
    for vlan_site, network, site_path in sites_to_build:
        network, inv_interfaces = inv_forward[vlan_site]
        vlan, site = vlan_site.split('.')
        # svn entries are [['pao1', 'ad', 'services' ...]

        # inv entires are [(IPv4Network('10.22.1.0/24'),
        # [<mdns.build_nics.Interface object at 0xab54250>]),...]

        # svn_entries are [('baz.bar.scl3.mozilla.com.', '10.22.85.212'),
        # ('foo.bar.scl3.mozilla.com.', '64.245.223.118'), ... ]


        # This is where we loose the 'vlan' part of the site. It's no longer
        # important because inventory files are per site.
        site_path, inv_entries = final_records.setdefault(site,
                (site_path, set()))

        for intr in inv_interfaces:
            if not intr.has_dns_info():
                continue  # Don't event try
            for ip in intr.ips:
                # We need to collect all the entries in all the vlans into
                # the same site.
                # !!! This '.' is important!
                inv_entries.add((intr.hostname + ".", ip, intr))

    log("=" * 10 + " Final DNS data", DEBUG)
    for site, site_data in final_records.items():
        site_path, inv_entries = site_data
        # Inv entries are in (<'name'>, <'ip'>) form

        zone, svn_entries = svn_zones.get(site, None)

        if svn_entries is not None:
            raw_a_records = filter_forward_conflicts(svn_entries, inv_entries,
                    site_path)
            clean_a_records = []
            for name, ip, intr in raw_a_records:
                cname_conflict = False
                for dns_name, ttl, dns_data in zone.iterate_rdatas('CNAME'):
                    cname = dns_name.to_text()
                    cdata = dns_data.to_text()
                    # This is madness, but it must be done.
                    if cname == name:
                        log("'{0}  A {1}' would conflict with '{2}   CNAME {3}', This "
                                "A record will not be included in the build "
                                "output.".format(name, ip, cname, cdata),
                                WARNING)
                        log("^ The system the conflict belongs to: "
                                "{0}".format(print_system(intr.system)))
                        cname_conflict = True
                if not cname_conflict:
                    clean_a_records.append((name, ip, intr))

        else:
            log("Couldn't find site {0} in svn".format(site),
                    WARNING)
            continue


        generate_forward_inventory_data_file(site, clean_a_records, site_path)

def generate_reverse_inventory_data_file(network, records, network_file):
    inventory_file = '{0}.inventory'.format(network_file)
    inv_fd = open(inventory_file, 'w+')
    try:
        log(";---------- PTR records for {0} (in file {1})\n".format(network,
                inventory_file), BUILD)
        template = "{dnsip:50} {rclass:10} {rtype:15} {name:7}\n"
        for dnsip, name in records:
            info = {'dnsip':dnsip, 'rclass':"IN", 'rtype':'PTR', 'name':name}
            log(template.format(**info), BUILD)
            inv_fd.write(template.format(**info))
        # Bump the soa in network file
        increment_soa(network_file)
        # Insure that the inventory file is included.
        ensure_include(network_file, 'reverse', inventory_file)
    except Exception, e:
        pdb.set_trace()
        log(str(e), ERROR)
    finally:
        inv_fd.close()

    if DEBUG == True:
        pp.pprint(records)

def generate_forward_inventory_data_file(site, records, site_path):
    inventory_file = os.path.join(site_path, 'inventory')
    private_file = os.path.join(site_path, 'private')
    soa_file = os.path.join(site_path, 'SOA')

    inv_fd = open(inventory_file, 'w+')

    # Because the interface objects are in records at this point, we have to
    # take them out before we remove duplicates.
    a_records = [ (name, address) for name, address, intr in records ]
    a_records = set(a_records)
    try:
        log(";---------- A records for {0} (in file {1})\n".format(site,
                site_path), BUILD)
        template = "{name:50} {rclass:10} {rtype:15} {address:7}\n"
        for name, address in a_records:
            info = {'name':name, 'rclass':"IN", 'rtype':'A', 'address':address}
            inv_fd.write(template.format(**info))
            log(template.format(**info), BUILD)
        # Bump the soa
        increment_soa(soa_file)
        # Insure that the inventory file is included.
        ensure_include(private_file, 'forward', inventory_file)
    except Exception, e:
        pdb.set_trace()
        log(str(e), ERROR)
    finally:
        inv_fd.close()

    if DEBUG == True:
        pp.pprint(records)

def filter_forward_conflicts(svn_records, inv_entries, site):
    """
    :param svn_records: All interfaces in the private file.
    :type svn_records: list

    :param inventory_interfaces: All interfaces in the inventory KV store.
    :type invnetory_interfaces: list

    """
    no_conflict_entries = []
    for name, ip, intr in inv_entries:
        if (name, ip) in svn_records:
            log("System {0} (interface: {1}, {2}) has conflict"
                .format(intr.system, ip, name), INFO)
        else:
            no_conflict_entries.append((name, ip, intr))

    return no_conflict_entries

def analyse_svn(forward, reverse):

    # forward_prime
    forward_p = set()
    for site, values in forward.iteritems():
        # Transform foward to look like reverse so we can use sets. Nifty
        # python sets are nifty.
        rzone, records = values
        for name, ip in records:
            if not ip.startswith('10'):
                continue
            if name.find('unused') > -1:
                # Don't care
                continue
            if name.find('sjc1') > -1:
                # Don't care
                continue
            dnsip = ip2dns_form(ip)
            forward_p.add((dnsip, name))

    # Make reverse_p
    reverse_p = set()
    for site, site_data in reverse.iteritems():
        site_path, values = site_data
        rzone, records = values
        for dnsip, name in records:
            if not dns2ip_form(dnsip).startswith('10'):
                continue
            if name.find('unused') > -1:
                # Don't care
                continue
            if name.find('sjc1') > -1:
                # Don't care
                continue
            reverse_p.add((dnsip, name))

    print ("PTR records in sysadmins/dnsconfig/ip-addr/ with no matching A "
        "record in sysadmins/dnsconfig/zones/mozilla.com")
    for dnsip, name in reverse_p.difference(forward_p):
        template = "{dnsip:50} {rclass:10} {rtype:15} {name:7}"
        info = {'dnsip':dnsip, 'rclass':"IN", 'rtype':'PTR', 'name':name}
        print template.format(**info)

    print ("A records in sysadmins/dnsconfig/zones/mozilla.com with no "
        "matching PTR record in sysadmins/dnsconfig/ip-addr/")
    for dnsip, name in forward_p.difference(reverse_p):
        address = dns2ip_form(dnsip)
        template = "{name:50} {rclass:10} {rtype:15} {address:7}"
        info = {'name':name, 'rclass':"IN", 'rtype':'A', 'address':address}
        print template.format(**info)
