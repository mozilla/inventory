import subprocess
import sys
import os
import pdb
import itertools
from dns import zone
from dns.zone import NoSOA

RELATIVE_PATH = "/home/juber/sysadmins/dnsconfig/"


def resolve(name, ns, rdclass="all"):
    proc = subprocess.Popen(["dig", "@{0}".format(ns), name, rdclass,
        "+short"], stdout=subprocess.PIPE)
    x = proc.communicate()[0]
    x = x.split('\n')
    x = '\n'.join(sorted(x))
    return x


def collect_svn_zone(root_domain, zone_path, relative_zone_path):
    cwd = os.getcwd()
    os.chdir(relative_zone_path)
    rzone = zone.from_file(zone_path, root_domain, relativize=False)
    os.chdir(cwd)
    return rzone


def check_rdtype(zone, nss, rdtype):
    for (name, ttl, rdata) in zone.iterate_rdatas(rdtype):
        name = name.to_text()
        if name == "sitespect.mozilla.com":
            pdb.set_trace()
        results = []
        for ns in nss:
            res = resolve(name, ns, rdclass=rdtype)
            if res.strip('\n').startswith("unused"):
                continue
            results.append(res)
        if len(set(results)) > 1:
            if results[0] != "":
                the_rest_are_empty = True
                for result in results[1:]:
                    if result:
                        the_rest_are_empty = False
                if the_rest_are_empty:
                    # We don't care that our nameserver has more info than the
                    # others. We only care if the data is different or our NS
                    # has _less_ info.
                    continue
            print "------------------------------------"
            print "Found differences for {0} {1}:".format(rdtype, name)

            for ns, result in itertools.izip(nss, results):
                print "{0} returned:\n-->\n{1}\n<--".format(ns,
                        result.strip('\n'))


def diff_nameservers(nss, zone_name, zone_file):
    try:
        zone = collect_svn_zone(zone_name, zone_file, RELATIVE_PATH)
    except NoSOA, e:
        return
    if zone_name.endswith('in-addr.arpa'):
        # Don't check for MX's
        rdtypes = ["A", "AAAA", "CNAME", "NS", "SRV", "TXT", "PTR"]
    else:
        rdtypes = ["A", "AAAA", "CNAME", "NS", "MX", "SRV", "TXT", "PTR"]
    for rdtype in rdtypes:
        check_rdtype(zone, nss, rdtype)


if __name__ == "__main__":
    from to_validate import things
    for thing in things:
        zone_name = thing['zone_name']
        zone_file = thing['zone_file']
        nss = []
        ns1 = thing['ns1']
        nss.append(ns1)
        ns2 = thing['ns2']
        nss.append(ns2)

        print "="*60
        print("==== Checking {0} against {1} with for the zone {2} with file "
            "{3}".format(ns1, ns2, zone_name, zone_file))
        print "="*60
        diff_nameservers(nss, zone_name, zone_file)
