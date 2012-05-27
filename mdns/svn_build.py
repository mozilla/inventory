import os
import pdb
from stat import *
import stat
import dns
from dns import zone
import pprint

pp = pprint.PrettyPrinter(indent=2)


MOZ_SITE_PATH = "/home/uberj/dns_data/zones/mozilla.com/"
REV_SITE_PATH = "/home/uberj/dns_data/zones/in-addr/"
ZONE_PATH = "/home/uberj/dns_data/"
SITE_IGNORE = []

def get_site_dirs(base_dir):
    if os.access(base_dir, os.R_OK):
        site_dirs = os.listdir(base_dir)
    else:
        print "Can't access MOZ_SITE_PATH"
        site_dirs = None
    return site_dirs

def process_site(site, site_dir):
    print "===Processing site: {0}".format(site)
    for file_ in site_dir:
        if file_ == ".svn":
            continue
        if file_ == ".svn":
            continue
        if file_.endswith(".signed"):
            continue
        if file_.endswith(".split"):
            continue
        print file_

def is_valid_site_dir(site, site_dir):
    has_private, has_SOA = False, False

    if "private" in site_dir:
        has_private = True
    if "SOA" in site_dir:
        has_SOA = True

    if has_private and has_SOA:
        return True
    else:
        if not has_private:
            print "{0} is missing the 'private' data file.".format(site)
        if not has_SOA:
            print "{0} is missing the 'SOA' file.".format(site)
        return False

def get_zone_data(domain, filepath, dirpath, rtype=None):
    print "domain = '{0}'\nfilepath = '{1}'\ndirpath = '{2}'\n".format(domain, filepath, dirpath)
    cwd = os.getcwd()
    os.chdir(dirpath)
    if rtype is None:
        return None
    rzone = zone.from_file(filepath, domain, relativize=False)
    data = []
    for (name, ttl, rdata) in rzone.iterate_rdatas(rtype):
        data.append((str(name), str(rdata)))

    os.chdir(cwd)
    return data

def collect_moz_zones(MOZ_SITE_PATH):
    sites = {}
    for site in get_site_dirs(MOZ_SITE_PATH):

        if site == ".svn":
            continue
        if site in SITE_IGNORE:
            continue

        if MOZ_SITE_PATH[len(MOZ_SITE_PATH)-1] == '/':
            MOZ_SITE_PATH = MOZ_SITE_PATH[:-1]

        full_site_path = "{0}/{1}".format(MOZ_SITE_PATH, site)
        mode = os.stat(full_site_path).st_mode
        if stat.S_ISDIR(mode) == 0:
            # It's not a directory
            continue

        site_dir = os.listdir(full_site_path)
        print "=" * 10 + "Processing site: {0}".format(site)
        if is_valid_site_dir(site, site_dir):
            domain = "{0}.mozilla.com".format(site)
            site_zone_data = get_zone_data(domain,
                    "{0}/private".format(full_site_path), ZONE_PATH, 'A')
            sites[site] = site_zone_data
        else:
            print "[Invalid]"
            continue
    return sites

def collect_rev_zones(REV_SITE_PATH):
    sites = {}
    fail = False
    for site in get_site_dirs(REV_SITE_PATH):
        if site == ".svn":
            continue
        if site in SITE_IGNORE:
            continue

        if REV_SITE_PATH[len(REV_SITE_PATH)-1] == '/':
            REV_SITE_PATH = REV_SITE_PATH[:-1]

        almost_full_site_path = "{0}/{1}".format(REV_SITE_PATH, site)
        mode = os.stat(almost_full_site_path).st_mode
        if stat.S_ISDIR(mode) == 0:
            # It's not a directory
            continue
        for network in get_site_dirs(almost_full_site_path):
            if network == ".svn":
                # EVERYWHERE!
                continue
            if network == "SOA":
                # zones/in-addr/10.14/SOA
                continue
            if network == "README":
                # zones/in-addr/10.14/README
                continue
            print "=== Processing site: {0}".format(network)
            # Validate network, reverse it, and slap an 'in-addr.arpa' onto it.
            octets = network.split('.')
            rev_domain = []
            for octet in reversed(octets):
                if not octet.isdigit():
                    print ("[ERROR] Could not parse reverse domain name "
                            " from file {0}/{1}/{2}.".format(REV_SITE_PATH,
                            site, network))
                    fail = True
                rev_domain.append(octet)

            if fail:
                fail = False
                continue

            rev_domain = "{0}.IN-ADDR.ARPA".format('.'.join(rev_domain))
            print "DOMAIN: " + rev_domain
            full_network_path = "{0}/{1}/{2}".format(REV_SITE_PATH, site,
                                                    network)

            mode = os.stat(full_network_path).st_mode
            if stat.S_ISREG(mode) == 0:
                print "[ERROR] {0} is missing ti's 'SOA' file".format(site)
            try:
                site_zone_data = get_zone_data(rev_domain,
                        full_network_path, ZONE_PATH, 'PTR')
            except dns.zone.NoSOA:
                print "[ERROR] No SOA found for {0}".format(full_network_path)
                print ("domain = '{0}'\nREV_SITE_PATH = '{1}'\n"
                        "full_network_path = '{2}'\n".format(rev_domain,
                        REV_SITE_PATH, full_network_path))

            sites[network] = site_zone_data

    return sites


def get_moz_sites():
    sites = {}
    collect_moz_zones(sites, MOZ_SITE_PATH)
    return sites

def get_rev_sites():
    sites = {}
    collect_rev_zones(sites, REV_SITE_PATH)
    return sites

if __name__ == '__main__':
    sites1 = collect_rev_zones(REV_SITE_PATH)
    sites2 = collect_moz_zones(MOZ_SITE_PATH)
    pp.pprint(sites1)
    pp.pprint(sites2)
