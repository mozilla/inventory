import os
import pdb
from stat import *
import stat
import dns
from dns import zone
import pprint
import hashlib
import ipaddr
from settings import MOZ_SITE_PATH
from settings import REV_SITE_PATH
from settings import ZONE_PATH
from mdns.utils import *
import truth
from truth.models import Truth
pp = pprint.PrettyPrinter(indent=2)


SITE_IGNORE = []

def get_site_dirs(base_dir):
    if os.access(base_dir, os.R_OK):
        site_dirs = os.listdir(base_dir)
    else:
        log("Can't access svn_site_path", ERROR)
        site_dirs = None
    return site_dirs

def process_site(site, site_dir):
    log("=== Processing site: {0}".format(site), DEBUG)
    for file_ in site_dir:
        if file_ == ".svn":
            continue
        if file_ == ".svn":
            continue
        if file_.endswith(".signed"):
            continue
        if file_.endswith(".split"):
            continue
        log(file_, DEBUG)

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
            log("{0} is missing the 'private' data file.".format(site), WARNING)
        if not has_SOA:
            log("{0} is missing the 'SOA' file.".format(site), WARNING)
        return False

def get_zone_data(domain, filepath, dirpath, rtype=None):
    log("domain = '{0}'\nfilepath = '{1}'\ndirpath = '{2}'\n".format(domain,
        filepath, dirpath), DEBUG)
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

def collect_svn_zones(svn_site_path, relative_zone_path):
    """
    :param svn_site_path: Full path to where reverse sites live. Atm that is in
        dnsconfig/zones/in-addr
    :type svn_rev_site_path: str
    :param relative_zone_path: Full path to the root of where zone files live. This full
        path is used by the zone parser during '$INCLUDE' statements.
    :type relative_zone_path: str
    """

    sites = {}
    for site in get_site_dirs(svn_site_path):

        if site == ".svn":
            continue
        if site in SITE_IGNORE:
            continue

        if svn_site_path[len(svn_site_path)-1] == '/':
            svn_site_path = svn_site_path[:-1]

        full_site_path = "{0}/{1}".format(svn_site_path, site)
        # MEGA DERP: TODO, use os.path.join
        mode = os.stat(full_site_path).st_mode
        if stat.S_ISDIR(mode) == 0:
            # It's not a directory
            continue

        site_dir = os.listdir(full_site_path)
        log("=" * 10 + "Processing site: {0}".format(site), DEBUG)
        if is_valid_site_dir(site, site_dir):
            domain = "{0}.mozilla.com".format(site)
            site_zone_data = get_zone_data(domain,
                    "{0}/private".format(full_site_path), relative_zone_path, 'A')
            sites[site] = site_zone_data
        else:
            log("[Invalid] site dir for site {0}".format(site_dir), WARNING)
            continue
    return sites

def collect_rev_svn_zones(svn_rev_site_path, relative_zone_path):
    """
    :param svn_rev_site_path: Full path to where reverse sites live. Atm that is in
        dnsconfig/zones/in-addr
    :type svn_rev_site_path: str
    :param relative_zone_path: Full path to the root of where zone files live. This full
        path is used by the zone parser during '$INCLUDE' statements.
    :type relative_zone_path: str
    """
    sites = {}
    fail = False
    # Get data for all the sites. Eventually, we might just want to get a
    # subset of the sites.
    for site in get_site_dirs(svn_rev_site_path):
        if site == ".svn":
            continue
        if site in SITE_IGNORE:
            continue

        if svn_rev_site_path[len(svn_rev_site_path)-1] == '/':
            svn_rev_site_path = svn_rev_site_path[:-1]

        almost_full_site_path = "{0}/{1}".format(svn_rev_site_path, site)
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
            if network.endswith(".inventory"):
                # zones/in-addr/10.14/README
                continue
            log("=== Processing site: {0}".format(network), DEBUG)
            # Validate network, reverse it, and slap an 'in-addr.arpa' onto it.
            octets = network.split('.')
            rev_domain = []
            for octet in reversed(octets):
                if not octet.isdigit():
                    print ("Could not parse reverse domain name ",
                            "from file {0}/{1}/{2}.".format(svn_rev_site_path,
                            site, network), ERROR)
                    fail = True
                rev_domain.append(octet)

            if fail:
                fail = False
                continue

            rev_domain = "{0}.IN-ADDR.ARPA".format('.'.join(rev_domain))
            full_network_path = "{0}/{1}/{2}".format(svn_rev_site_path, site,
                                                    network)

            mode = os.stat(full_network_path).st_mode
            if stat.S_ISREG(mode) == 0:
                log("{0} is missing it's 'SOA' file".format(site),
                        ERROR)
            try:
                site_zone_data = get_zone_data(rev_domain,
                        full_network_path, relative_zone_path, 'PTR')
            except dns.zone.NoSOA:
                log("No SOA found for {0}".format(full_network_path),
                        ERROR)
                log("domain = '{0}'\nsvn_rev_site_path = '{1}'\n"
                        "full_network_path = '{2}'\n".format(rev_domain,
                        svn_rev_site_path, full_network_path), ERROR)

            sites[network] = (full_network_path, site_zone_data)

    return sites

def get_hash_store():
    hash_store, created = Truth.objects.get_or_create(name="dns_site_hash",
            description="Truth store for storing hashes of DNS data files in "
            "SVN. Don't edit these entries")
    if created:
        log("Created dns_site_hash")
    return hash_store

# This regex is wrong. it matches 256.256.256.256.
is_network_file = re.compile("^([0-9][0-9]?[0-9]?)\.([0-9][0-9]?[0-9]?)\.([0-9][0-9]?[0-9]?)$")
def get_reverse_svn_sites_changed(sites, site_path):
    """This function looks at every file in the in-addr/ directory in SVN and
    compares it to the full list of sites that *could* be built. If the network
    that the file represents and a file overlap *and* the file has been
    changed, the site will be added to sites_to_build.

    :param sites: The sites for which we are looking for changes in.
    :type sites: list
    :param site_path: Where sites are stored.
    :type site_path: str
    """
    hash_store = get_hash_store()
    files_to_check = []
    for network in os.listdir(site_path):
        network_dir = os.path.join(site_path, network)
        if not os.path.isdir(network_dir):
            continue
        for file_ in os.listdir(network_dir):
            if not is_network_file.match(file_):
                continue
            network_file = os.path.join(network_dir, file_)
            files_to_check.append((file_, network_file))

    sites_to_build = []
    for network, file_ in files_to_check:
        digest = hash_file(file_)
        kv_prev_digest = truth.models.KeyValue.objects.filter(truth=hash_store,
                key=file_)

        if kv_prev_digest and kv_prev_digest[0].value == digest:
            log("No changes in {0}".format(file_), INFO)
            continue
        elif kv_prev_digest and kv_prev_digest[0].value != digest:
            kv_prev_digest = kv_prev_digest[0]
            log("Changes in network {0}, file {1}".format(network, file_), INFO)
            # Fall through
        elif not kv_prev_digest:
            log("New file for network {0}, file {1}".format(network, file_), INFO)
            kv_prev_digest = truth.models.KeyValue(truth=hash_store,
                    key=file_, value=digest)

        # Even if the file isn't going to cause a site to be built, track
        # it's hash.
        kv_prev_digest.value = digest
        kv_prev_digest.save()

        for site_meta in sites:
            vlan_site, site_network_str, site_path = site_meta

            # Determine if the file_'s network intersects with the vlan
            # corresponding to this site.

            # !!!!! THERE COULD BE A BUG RIGHT HERE.
            # TODO Ask people about this.
            # If the class C network the file represents overlaps with a
            # network in a site, rebuild that site.
            network_file_str = network + ".0/24"  # Make sure it's a full class C
            network_file = ipaddr.IPv4Network(network_file_str)
            site_network = ipaddr.IPv4Network(site_network_str)

            if ipaddr.IPv4Network(network_file).overlaps(site_network):
                sites_to_build.append(site_meta)
                kv_prev_digest.value = digest
                kv_prev_digest.save()
                continue


    return sites_to_build

def hash_file(file_):
    fd = open(file_, 'r')
    hash_ = hashlib.md5()
    hash_.update(fd.read())
    digest = hash_.hexdigest()
    fd.close()
    return digest

def get_forward_svn_sites_changed(sites, site_path):
    """This function should return a list of sites that have been changed in
    SVN. It calculates which sites have changed by storing a hash of a file and
    then comparing the current file's hash to the stored hash during next time
    the build script runs.

    :param sites: The sites for which we are looking for changes in.
    :type sites: list
    :param site_path: Where sites are stored.
    :type site_path: str
    """

    hash_store = get_hash_store()

    files_to_check = []
    for site_meta in sites:
        vlan_site, network, site_path = site_meta
        vlan, site = vlan_site.split('.')
        for file_ in os.listdir(site_path):
            important_files = ['SOA', 'private', 'public']
            if file_ not in important_files:
                continue
            files_to_check.append((os.path.join(site_path, file_), site_meta))

    sites_to_build = []
    files_flaged_to_build = set()
    log("Checking for changes in the following files:", DEBUG)
    for file_, site_meta in files_to_check:
        vlan_site, network, site_path = site_meta
        vlan, site = vlan_site.split('.')
        if file_ in files_flaged_to_build:
            sites_to_build.append(site_meta)
            continue

        # Compute the hash
        digest = hash_file(file_)

        kv_prev_digest = truth.models.KeyValue.objects.filter(truth=hash_store,
                key=file_)
        if kv_prev_digest and kv_prev_digest[0].value == digest:
            log("No changes in {0}".format(file_), INFO)
            continue
        if kv_prev_digest and kv_prev_digest[0].value != digest:
            log("Changes in site {0}, file {1}".format(site, file_), INFO)
            sites_to_build.append(site_meta)
            files_flaged_to_build.add(file_)
            kv_prev_digest[0].value = digest
            kv_prev_digest[0].save()
            continue

        log("New file for site {0}, file {1}".format(site, file_), INFO)
        # We didn't find anything.
        kv = truth.models.KeyValue(truth=hash_store,
                key=file_, value=digest)
        kv.save()
        files_flaged_to_build.add(file_)
        sites_to_build.append(site_meta)


    # We didn't find a site
    return sites_to_build
