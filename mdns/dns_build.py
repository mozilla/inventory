from mdns.inventory_build import inventory_build_sites
from mdns.svn_build import collect_svn_zones, collect_rev_svn_zones
from mdns.svn_build import get_svn_sites_changed
from mdns.build_nics import *
from truth.models import Truth

from settings import MOZ_SITE_PATH
from settings import REV_SITE_PATH
from settings import ZONE_PATH

import os.path
import pprint

DEBUG = False

pp = pprint.PrettyPrinter(indent=2)

def get_all_forward_sites(site_path):
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

def do_dns_build():
    # The function get_all_sites should generate tuples like:
    #   ('<site-name>', '<network>', '<file_path_to_site_dir>')

    sites_to_build = set(get_all_forward_sites(MOZ_SITE_PATH))
    #sites_to_build = set(get_dns_scheduled_sites(MOZILLA_SITE_PATH))
    #sites_to_build.add(get_svn_sites_changed(
    #    get_all_forward_sites(MOZ_SITE_PATH)))

    inv_forward, inv_reverse = inventory_build_sites(sites_to_build)
    if DEBUG == True:
        print "=" * 10 + "Forward sites" + "=" * 10
        for site, data in inv_forward.items():
            print "-" * 10 + site
            network, entries = data
            for thing in entries:
                thing.pprint()

        print "=" * 10 + "Reverse sites" + "=" * 10
        for site, data in inv_reverse.items():
            print "-" * 10 + site
            for intr in data:
                thing.pprint()

    moz_zones = collect_svn_zones(MOZ_SITE_PATH, ZONE_PATH)
    #rev_zones = collect_rev_zones(REV_SITE_PATH, ZONE_PATH)


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

    print "=" * 10 + " Final DNS data"
    for site, site_data in final_records.items():
        site_path, inv_entries = site_data
        # Inv entries are in (<'name'>, <'ip'>) form

        svn_entries = moz_zones.get(site, None)

        if svn_entries is not None:
            a_records = filter_forward_conflicts(svn_entries, inv_entries,
                    site_path)
        else:
            print "[WARNING] Couldn't find site {0} in svn".format(site)
            continue

        print "-" * 10 + site

        generate_forward_inventory_data_file(site, a_records, site_path)


def generate_forward_inventory_data_file(site, records, site_path):
    inventory_file = os.path.join(site_path, 'inventory')
    private_file = os.path.join(site_path, 'private')
    #fd = open(inventory_file, 'w+')
    try:
        for name, address, intr in records:
            print ("{name:50} {rclass:10} {rtype:15} {address:7}\n".format(
            #fd.write(("{name:50} {rclass:10} {rtype:15} {address:7}\n".format(
                name=name, rclass="IN", rtype='A', address=address)),
    except Exception, e:
        print str(e)
    finally:
        pass
        #fd.close()

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
            print ("[INFO] System {0} (interface: {1}, {2}) has conflict"
                .format(intr.system, ip, name))
        else:
            no_conflict_entries.append((name, ip, intr))

    return no_conflict_entries
