from mdns.inventory_build import inventory_build_sites
from mdns.svn_build import collect_moz_zones, collect_rev_zones
from mdns.build_nics import *


import pprint

pp = pprint.PrettyPrinter(indent=2)

MOZ_SITE_PATH = "/home/uberj/dns_data/zones/mozilla.com/"
REV_SITE_PATH = "/home/uberj/dns_data/zones/in-addr/"
ZONE_PATH = "/home/uberj/dns_data/"
SITE_IGNORE = []

def do_dns_build():
    sites = [
            ('dmz.scl3', '10.22.1.0/24'),
            ('sandbox.scl3', '10.22.76.0/24'),
            ('mail.scl3', '10.22.77.0/24'),
            ('webapp.scl3', '10.22.81.0/24'),
            ('private.scl3', '10.22.75.0/24'),
            ('db.scl3', '10.22.70.0/24'),
            ('webapp.phx1', '10.8.81.0/24'),
        ]
    inv_forward, inv_reverse = inventory_build_sites(sites)
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

    moz_zones = collect_moz_zones(MOZ_SITE_PATH)
    #rev_zones = collect_rev_zones(REV_SITE_PATH)

    final_sites = {} # These are the records we use to build sites.
    for site, inv_entries in inv_forward.items():
        # svn entries are [['pao1', 'ad', 'services' ...]

        # inv entires are [(IPv4Network('10.22.1.0/24'),

        # [<mdns.build_nics.Interface object at 0xab54250>]),...]
        # site is <vlan>.<DC>
        vlan, site = site.split('.')

        # svn_entries are [('baz.bar.scl3.mozilla.com.', '10.22.85.212'),
        # ('foo.bar.scl3.mozilla.com.', '64.245.223.118'), ... ]
        svn_entries = moz_zones.get(site, None)


        if svn_entries is not None:
            # I wrote this drunk.
            there = final_sites.get(site, False)
            if not there:
                final_sites[site] = []
            final_sites[site] += filter_forward_conflicts(svn_entries, inv_entries,
                    site)
        else:
            print "[WARNING] Couldn't find site {0} in svn".format(site)

    print "=" * 10 + "Final DNS data"
    for site, data in final_sites.items():
        print "-" * 10 + site
        for thing in data:
            print thing.hostname + "   " + str(thing.ips)

def filter_forward_conflicts(private_interfaces, inventory_site, site):
    """
    :param private_interfaces: All interfaces in the private file.
    :type private_interfaces: list

    :param inventory_interfaces: All interfaces in the inventory KV store.
    :type invnetory_interfaces: list

    """
    network, inventory_interfaces = inventory_site
    no_conflict_intrs = []
    for interface in inventory_interfaces:

        # If it can't handle it. Don't try.
        if not interface.has_dns_info():
            continue

        #if interface in svn_interfaces:
        for ip in interface.ips:
            if (interface.hostname+".", ip) in private_interfaces:
                print ("System {0} ({1}, {2}) has conflict "
                    .format(interface.system, ip, interface.hostname))
            else:
                no_conflict_intrs.append(interface)

    return no_conflict_intrs
