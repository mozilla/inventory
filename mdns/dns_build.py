from django.core.exceptions import ObjectDoesNotExist, ValidationError
from truth.models import Truth

from mdns.inventory_build import inventory_build_sites
from mdns.svn_build import collect_svn_zones, collect_rev_svn_zones
from mdns.svn_build import collect_svn_zone, collect_rev_svn_zone
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
from core.network.models import Network
from core.interface.static_intr.models import StaticInterface

from mozdns.address_record.models import AddressRecord
from mozdns.cname.models import CNAME
from mozdns.domain.models import Domain
from mozdns.mx.models import MX
from mozdns.nameserver.models import Nameserver
from mozdns.ptr.models import PTR
from mozdns.soa.models import SOA
from mozdns.srv.models import SRV
from mozdns.tests.view_tests import random_label
from mozdns.txt.models import TXT
from mozdns.domain.utils import *
from mozdns.ip.utils import ip_to_domain_name
from mozdns.ip.models import ipv6_to_longs
from mozdns.view.models import View

import os.path
import pprint
import re

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
    intr_certainty = False
    exintr = None
    for intr in intrs:
        if intr.fqdn.startswith(nic.hostname):
            log("Found Interface {0} that matches nic.ip {1} and partially "
                "nic.hostname {2}".format(intr, nic.ips[0], nic.hostname))
            intr_certainty = True
            if exintr:
                log("Found another Interface {0} that looks a lot like {1}, "
                    "while searching for nic.ip {2} and nic.hostname {3}."
                    "{2}".format(intr, exintr, nic.ips[0], nic.hostname),
                    WARNING)
            exintr = intr

    # Ok, we have records with the same ip. Look for name matches.
    addr_certainty = False
    exaddr = None
    for addr in addrs:
        if addr.fqdn.startswith(nic.hostname):
            # The ip patches and the hostname of the nic lines up with the
            # name on the Address Record.
            addr_certainty = True
            log("Found A {0} that matches nic.ip {1} and partially "
                "nic.hostname {2}".format(addr, nic.ips[0], nic.hostname))
            if exaddr:
                log("Found another A record {0} that looks a lot like {1}, "
                    "while searching for nic.ip {2} and nic.hostname {3}."
                    "{2}".format(addr, exaddr, nic.ips[0], nic.hostname),
                    WARNING)
            exaddr = addr

    # Search in the ptr space.
    ptr_certainty = False
    exptr = None
    for ptr in ptrs:
        if ptr.name.startswith(nic.hostname):
            log("Found PTR {0} that matches nic.ip {1} and partially "
                "nic.hostname {2}".format(ptr, nic.ips[0],
                 nic.hostname))
            ptr_certainty = True
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

def do_dns_build():
    # The function get_all_sites should generate tuples like:
    #   ('<site-name>', '<network>', '<file_path_to_site_dir>')


    #sites_to_build = set(get_all_sites(MOZ_SITE_PATH))
    #sites_to_build = set()

    #changed_ui = set(get_ui_sites_changed(all_sites))
    #sites_to_build = sites_to_build.union(changed_ui)

    #changed_forward = set(get_forward_svn_sites_changed(all_sites,
    #    MOZ_SITE_PATH))
    #sites_to_build = sites_to_build.union(changed_forward)

    #changed_reverse = set(get_reverse_svn_sites_changed(all_sites,
    #    REV_SITE_PATH))
    #sites_to_build = sites_to_build.union(changed_reverse)
    svn_zones = collect_svn_zones(MOZ_SITE_PATH, ZONE_PATH)
    rev_svn_zones = collect_rev_svn_zones(REV_SITE_PATH, ZONE_PATH)


    populate_forward_dns(svn_zones)
    populate_reverse_dns(rev_svn_zones)

def create_domain(name, ip_type=None, delegated=False):
    if ip_type is None:
        ip_type = '4'
    if name in ('arpa', 'in-addr.arpa', 'ipv6.arpa'):
        pass
    else:
        name = ip_to_domain_name(name, ip_type=ip_type)
    d = Domain.objects.get_or_create(name = name, delegated=delegated)
    return d

def do_zone_build(ztype, view, root_domain, zone_path):

    view_obj, _ = View.objects.get_or_create(name=view)
    if ztype == 'forward':
        svn_zones = {root_domain.replace('mozilla.com', ''):((collect_svn_zone(root_domain, zone_path,
            ZONE_PATH)), '')}
        populate_forward_dns(svn_zones, view=view_obj)
    elif ztype == 'reverse':
        rev_svn_zones = {root_domain:('', ((collect_rev_svn_zone(root_domain, zone_path,
            ZONE_PATH)), ''))}
        populate_reverse_dns(rev_svn_zones, view=view_obj)
    else:
        print "Slob"

def zone_build_from_config(job=None):
    """
    This is so fucked. We can't run all of these at once because it causes the
    box to run out of memory.
    """
    if not job:
        print "Jobs are: external, dc, private_reverse"
        return
    import dns
    if job == "external":
        from mdns.migrate.zone_configs.external import external
        for config in external:
            zone_path = config['path']
            root_domain = config['zone_name']
            name_reversed = config['name_reversed']
            ztype = config['direction']
            view = config['view']
            relative_path = config['relative_path']
            view_obj, _ = View.objects.get_or_create(name=view)
            try:
                if ztype == 'f':
                    print view
                    svn_zone = collect_svn_zone(root_domain, zone_path, ZONE_PATH)
                    populate_forward_dns(svn_zone, root_domain, view=view_obj)
                    del svn_zone
                if ztype == 'r':
                    rev_svn_zones = {root_domain:('', ((collect_rev_svn_zone(root_domain, zone_path,
                        ZONE_PATH)), ''))}
                    populate_reverse_dns(rev_svn_zones, view=view_obj)
            except dns.zone.NoSOA, e:
                print "----------------------"
                print "ERROR: NoSOA()"
                print zone_path
                print "----------------------"
        return

    if job == "zones":
        from mdns.migrate.zone_configs.zones import zones
        for config in zones:
            zone_path = config['path']
            root_domain = config['zone_name']
            name_reversed = config['name_reversed']
            ztype = config['direction']
            view = config['view']
            relative_path = config['relative_path']
            view_obj, _ = View.objects.get_or_create(name=view)
            if ztype == 'f':
                svn_zone = collect_svn_zone(root_domain, zone_path, ZONE_PATH)
                populate_forward_dns(svn_zone, root_domain, view=view_obj)
                del svn_zone
        return

    if job == "net":
        from mdns.migrate.zone_configs.mozilla_net import mozilla_net
        for config in mozilla_net:
            zone_path = config['path']
            root_domain = config['zone_name']
            name_reversed = config['name_reversed']
            ztype = config['direction']
            view = config['view']
            relative_path = config['relative_path']
            view_obj, _ = View.objects.get_or_create(name=view)
            if ztype == 'f':
                svn_zone = collect_svn_zone(root_domain, zone_path, ZONE_PATH)
                populate_forward_dns(svn_zone, root_domain, view=view_obj)
                del svn_zone
        return

    try:
        if job == "mozilla_org":
            from mdns.migrate.zone_configs.mozilla_org import mozilla_org
            for config in mozilla_org:
                zone_path = config['path']
                root_domain = config['zone_name']
                name_reversed = config['name_reversed']
                ztype = config['direction']
                view = config['view']
                relative_path = config['relative_path']
                view_obj, _ = View.objects.get_or_create(name=view)
                if ztype == 'f':
                    svn_zone = collect_svn_zone(root_domain, zone_path, ZONE_PATH)
                    populate_forward_dns(svn_zone, root_domain, view=view_obj)
                    del svn_zone
            return
    except Exception, e:
        pdb.set_trace()
        pass

    if job == "dc":
        from mdns.migrate.zone_configs.mozilla_com_dc_zone_config import mozilla_com_dcs
        for config in mozilla_com_dcs:
            zone_path = config['path']
            root_domain = config['zone_name']
            name_reversed = config['name_reversed']
            ztype = config['direction']
            view = config['view']
            relative_path = config['relative_path']
            view_obj, _ = View.objects.get_or_create(name=view)
            if ztype == 'f':
                svn_zone = collect_svn_zone(root_domain, zone_path, ZONE_PATH)
                populate_forward_dns(svn_zone, root_domain, view=view_obj)
                del svn_zone
        return

    if job == "private_reverse":
        from mdns.migrate.zone_configs.private_reverse import private_reverse
        for config in private_reverse:
            zone_path = config['path']
            root_domain = config['zone_name']
            name_reversed = config['name_reversed']
            ztype = config['direction']
            view = config['view']
            relative_path = config['relative_path']
            view_obj, _ = View.objects.get_or_create(name=view)
            if ztype == 'r':
                rev_svn_zones = {root_domain:('', ((collect_rev_svn_zone(root_domain, zone_path,
                    ZONE_PATH)), ''))}
                populate_reverse_dns(rev_svn_zones, view=view_obj)


def populate_reverse_dns(rev_svn_zones, view=None):
    arpa = create_domain( name = 'arpa')
    i_arpa = create_domain( name = 'in-addr.arpa')
    i6_arpa = create_domain( name = 'ipv6.arpa')

    for site, data in rev_svn_zones.iteritems():
        site_path, more_data = data
        zone, records = more_data
        print "-" * 15 + " " + site

        for (name, ttl, rdata) in zone.iterate_rdatas('SOA'):
            print str(name) + " SOA " + str(rdata)
            exists = SOA.objects.filter(minimum=rdata.minimum,
                    contact=rdata.rname.to_text().strip('.'),
                    primary=rdata.mname.to_text().strip('.'),
                    comment="SOA for {0}.in-addr.arpa".format(
                        '.'.join(reversed(site.split('.')))))
            if exists:
                soa = exists[0]
            else:
                soa = SOA(serial=rdata.serial, minimum=rdata.minimum,
                        contact=rdata.rname.to_text().strip('.'),
                        primary=rdata.mname.to_text().strip('.'),
                        comment="SOA for {0}.in-addr.arpa".format(
                            '.'.join(reversed(site.split('.')))))
                soa.clean()
                soa.save()
            name = name.to_text().replace('.IN-ADDR.ARPA.','')
            domain_split = list(reversed(name.split('.')))
            for i in range(len(domain_split)):
                domain_name = domain_split[:i+1]
                rev_name = ip_to_domain_name('.'.join(domain_name), ip_type='4')
                base_domain, created = Domain.objects.get_or_create(name=rev_name)

            #null_all_soas(base_domain)
            base_domain.soa = soa
            base_domain.save()
            #set_all_soas(base_domain, soa)

        for (name, ttl, rdata) in zone.iterate_rdatas('NS'):
            name = name.to_text().strip('.')
            name = name.replace('.IN-ADDR.ARPA','')
            name = name.replace('.in-addr.arpa','')
            print str(name) + " NS " + str(rdata)
            domain_name = '.'.join(list(reversed(name.split('.'))))
            domain = ensure_rev_domain(domain_name)
            ns, _ = Nameserver.objects.get_or_create(domain=domain,
                    server=rdata.target.to_text().strip('.'))
            if view:
                ns.views.add(view)
                ns.save()
        for (name, ttl, rdata) in zone.iterate_rdatas('PTR'):
            ip_str = name.to_text().strip('.')
            ip_str = ip_str.replace('.IN-ADDR.ARPA','')
            ip_str = ip_str.replace('.in-addr.arpa','')
            ip_str= '.'.join(list(reversed(ip_str.split('.'))))
            fqdn = rdata.target.to_text().strip('.')
            if fqdn.startswith('unused'):
                print "Skipping "+ip_str+" "+fqdn
                continue
            if ip_str == '10.2.171.IN':
                log("Skipping 10.2.171.IN", WARNING)
                continue
            print str(name) + " PTR " + str(fqdn)
            ptr = PTR.objects.filter(name = fqdn, ip_str = ip_str, ip_type='4')
            if ptr:
                continue
            else:
                try:
                    ptr = PTR(name = fqdn, ip_str = ip_str, ip_type='4')
                    ptr.full_clean()
                    ptr.save()
                    if view:
                        ptr.views.add(view)
                        ptr.save()
                except Exception, e:
                    pdb.set_trace()
                    pass

    for (name, ttl, rdata) in zone.iterate_rdatas('MX'):
        name = name.to_text().strip('.')
        print str(name) + " MX " + str(rdata)
        exists_domain = Domain.objects.filter(name=name)
        if exists_domain:
            label = ''
            domain = exists_domain[0]
        else:
            label = name.split('.')[0]
            domain_name = '.'.join(name.split('.')[1:])
            domain = ensure_domain(domain_name)
        priority = rdata.preference
        server = rdata.exchange.to_text().strip('.')
        mx, _ = MX.objects.get_or_create(label=label, domain=domain,
                server= server, priority=priority, ttl="3600")
        if view:
            mx.views.add(view)
            try:
                mx.save()
                mx.views.all()
            except Exception, e:
                pdb.set_trace()

        """
        for (name, ttl, rdata) in zone.iterate_rdatas('CNAME'):
            name = name.to_text().strip('.')
            print str(name) + " CNAME " + str(rdata)
            rev_name = ip_to_domain_name(name, ip_type='4')
            exists_domain = Domain.objects.filter(name=rev_name)
            if exists_domain:
                label = ''
                domain = exists_domain[0]
            else:
                label = name.split('.')[0]
                domain_name = name.split('.')[1:]
                domain = ensure_domain('.'.join(domain_name))
            data = rdata.target.to_text().strip('.')

            if not CNAME.objects.filter(label = label, domain = domain,
                    data = data).exists():
                cn = CNAME(label = label, domain = domain,
                        data = data)
                cn.full_clean()
                cn.save()
        """
        #set_all_soas(base_domain, base_domain.soa)

def ensure_rev_domain(name):
    parts = name.split('.')
    domain_name = ''
    for i in range(len(parts)):
        domain_name = domain_name + '.' + parts[i]
        domain_name = domain_name.strip('.')
        rev_name = ip_to_domain_name(domain_name, ip_type='4')
        domain, created = Domain.objects.get_or_create(name=
                rev_name)
        if domain.master_domain and domain.master_domain.soa:
            pass
            #domain.soa = domain.master_domain.soa
            #domain.save()

    return domain

def set_all_soas(domain, soa):
    for child_domain in domain.domain_set.all():
        child_domain.soa = soa
        child_domain.save()
        set_all_soas(child_domain, soa)

def null_all_soas(domain):
    for child_domain in domain.domain_set.all():
        null_all_soas(child_domain)
        child_domain.soa = None
        child_domain.save()

def populate_forward_dns(zone, root_domain, view=None):
    for (name, ttl, rdata) in zone.iterate_rdatas('SOA'):
        print str(name) + " SOA " + str(rdata)
        exists = SOA.objects.filter(minimum=rdata.minimum,
                contact=rdata.rname.to_text().strip('.'),
                primary=rdata.mname.to_text().strip('.'), comment="SOA for"
                " {0}".format(root_domain))
        if exists:
            soa = exists[0]
        else:
            soa = SOA(serial=rdata.serial, minimum=rdata.minimum,
                    contact=rdata.rname.to_text().strip('.'),
                    primary=rdata.mname.to_text().strip('.'), comment="SOA for"
                    " {0}".format(root_domain))
            soa.clean()
            soa.save()
        domain_split = list(reversed(name.to_text().strip('.').split('.')))
        for i in range(len(domain_split)):
            domain_name = domain_split[:i+1]
            base_domain, created = Domain.objects.get_or_create(name=
                    '.'.join(list(reversed(domain_name))))

        null_all_soas(base_domain)
        base_domain.soa = soa
        base_domain.save()
        set_all_soas(base_domain, soa)

    names = []
    for (name, ttl, rdata) in zone.iterate_rdatas('A'):
        names.append((name.to_text().strip('.'), rdata))
    sorted_names = list(sorted(names, cmp=lambda n1, n2: -1 if
        len(n1[0].split('.'))> len(n2[0].split('.')) else 1))

    for name, rdata in sorted_names:
        print str(name) + " A " + str(rdata)
        exists_domain =  Domain.objects.filter(name=name)
        if exists_domain:
            label = ''
            domain = exists_domain[0]
        else:
            label = name.split('.')[0]
            if label.find('unused') != -1:
                continue
            parts = list(reversed(name.split('.')[1:]))
            domain_name = ''
            for i in range(len(parts)):
                domain_name = parts[i] + '.' + domain_name
                domain_name = domain_name.strip('.')
                # We need to check for A records who have a name with this
                # domain.
                addrs = AddressRecord.objects.filter(fqdn=domain_name,
                            ip_type='4')
                clober_objects = []
                if addrs:
                    for exists_a in addrs:
                        # It got here. It exists
                        need_to_recreate_a = True
                        ip_str = exists_a.ip_str
                        exists_a.delete(check_cname=False)
                        a = AddressRecord(label='', ip_str=ip_str, ip_type='4')
                        clober_objects.append(a)
                domain, created = Domain.objects.get_or_create(name=
                        domain_name)
                for a in clober_objects:
                    a.domain = domain
                    a.clean()
                    try:
                        a.save()
                    except Exception, e:
                        pdb.set_trace()
                        pass

                if created and domain.master_domain and domain.master_domain.soa:
                    #domain.soa = domain.master_domain.soa
                    #domain.save()
                    null_all_soas(domain)
                    set_all_soas(domain, domain.master_domain.soa)
        a, _ = AddressRecord.objects.get_or_create( label = label,
            domain=domain, ip_str=rdata.to_text(), ip_type='4')
        if view:
            a.views.add(view)
            try:
                a.save()
            except Exception, e:
                pdb.set_trace()
                pass

    for (name, ttl, rdata) in zone.iterate_rdatas('AAAA'):
        name = name.to_text().strip('.')
        print str(name) + " AAAA " + str(rdata)
        exists_domain =  Domain.objects.filter(name=name)
        if exists_domain:
            label = ''
            domain = exists_domain[0]
        else:
            label = name.split('.')[0]
            if label.find('unused') != -1:
                continue
            parts = list(reversed(name.split('.')[1:]))
            domain_name = ''
            for i in range(len(parts)):
                domain_name = parts[i] + '.' + domain_name
                domain_name = domain_name.strip('.')
                # We need to check for A records who have a name with this
                # domain.
                addrs = AddressRecord.objects.filter(fqdn=domain_name)
                clober_objects = []
                if addrs:
                    for exists_a in addrs:
                        # It got here. It exists
                        need_to_recreate_a = True
                        ip_str = exists_a.ip_str
                        ip_type = exists_a.ip_type
                        exists_a.delete(check_cname=False)
                        a = AddressRecord(label='', ip_str=ip_str,
                                ip_type=ip_type)
                        clober_objects.append(a)
                domain, created = Domain.objects.get_or_create(name=
                        domain_name)
                for a in clober_objects:
                    a.domain = domain
                    a.clean()
                    try:
                        a.save()
                    except Exception, e:
                        pdb.set_trace()
                        pass

                if created and domain.master_domain and domain.master_domain.soa:
                    #domain.soa = domain.master_domain.soa
                    #domain.save()
                    null_all_soas(domain)
                    set_all_soas(domain, domain.master_domain.soa)
        ip_upper, ip_lower = ipv6_to_longs(rdata.to_text())
        if AddressRecord.objects.filter(label=label,
                domain=domain, ip_upper=ip_upper, ip_lower=ip_lower,
                ip_type='6').exists():
            a = AddressRecord.objects.get(label=label,
                    domain=domain, ip_type='6', ip_upper=ip_upper,
                    ip_lower=ip_lower)
        else:
            a, _ = AddressRecord.objects.get_or_create(label=label,
                    domain=domain, ip_str=rdata.to_text(), ip_type='6')
        if view:
            a.views.add(view)
            try:
                a.save()
            except Exception, e:
                pdb.set_trace()
                pass


    for (name, ttl, rdata) in zone.iterate_rdatas('NS'):
        name = name.to_text().strip('.')
        print str(name) + " NS " + str(rdata)
        domain_name = '.'.join(name.split('.')[1:])
        domain = ensure_domain(name)
        ns, _ = Nameserver.objects.get_or_create(domain=domain,
                server=rdata.target.to_text().strip('.'))
        if view:
            ns.views.add(view)
            ns.save()

    for (name, ttl, rdata) in zone.iterate_rdatas('MX'):
        name = name.to_text().strip('.')
        print str(name) + " MX " + str(rdata)
        exists_domain = Domain.objects.filter(name=name)
        if exists_domain:
            label = ''
            domain = exists_domain[0]
        else:
            label = name.split('.')[0]
            domain_name = '.'.join(name.split('.')[1:])
            domain = ensure_domain(domain_name)
        priority = rdata.preference
        server = rdata.exchange.to_text().strip('.')
        mx, _ = MX.objects.get_or_create(label=label, domain=domain,
                server= server, priority=priority, ttl="3600")
        if view:
            mx.views.add(view)
            try:
                mx.save()
                mx.views.all()
            except Exception, e:
                pdb.set_trace()

    for (name, ttl, rdata) in zone.iterate_rdatas('CNAME'):
        name = name.to_text().strip('.')
        print str(name) + " CNAME " + str(rdata)
        exists_domain = Domain.objects.filter(name=name)
        if exists_domain:
            label = ''
            domain = exists_domain[0]
        else:
            label = name.split('.')[0]
            domain_name = name.split('.')[1:]
            domain = ensure_domain('.'.join(domain_name))
        data = rdata.target.to_text().strip('.')

        if not CNAME.objects.filter(label = label, domain = domain,
                data = data).exists():
            cn = CNAME(label = label, domain = domain,
                    data = data)
            cn.full_clean()
            cn.save()
            if view:
                cn.views.add(view)
                cn.save()
    # TODO, records not done yet. TXT, SSHFP, AAAA
    # Create list
    for (name, ttl, rdata) in zone.iterate_rdatas('TXT'):
        name = name.to_text().strip('.')
        print str(name) + " TXT " + str(rdata)
        exists_domain = Domain.objects.filter(name=name)
        if exists_domain:
            label = ''
            domain = exists_domain[0]
        else:
            label = name.split('.')[0]
            domain_name = name.split('.')[1:]
            domain = ensure_domain('.'.join(domain_name))
        data = rdata.to_text().strip('"')

        if not TXT.objects.filter(label = label, domain = domain,
                txt_data = data).exists():
            txt = TXT(label = label, domain = domain,
                    txt_data = data)
            txt.full_clean()
            txt.save()
            if view:
                txt.views.add(view)
                txt.save()

    for (name, ttl, rdata) in zone.iterate_rdatas('SSHFP'):
        name = name.to_text().strip('.')
        pdb.set_trace()
        print str(name) + " SSHFP " + str(rdata)

    for (name, ttl, rdata) in zone.iterate_rdatas('SRV'):
        target = rdata.target.to_text().strip('.')
        if target == "":
            target = "."
        port = rdata.port
        weight = rdata.weight
        prio = rdata.priority
        name = name.to_text().strip('.')
        print str(name) + " SRV " + str(rdata)
        exists_domain = Domain.objects.filter(name=name)
        if exists_domain:
            label = ''
            domain = exists_domain[0]
        else:
            label = name.split('.')[0]
            domain_name = name.split('.')[1:]
            domain = ensure_domain('.'.join(domain_name))

        if not SRV.objects.filter(label = label, domain = domain,
                target=target, port=port, weight=weight,
                priority=prio).exists():
            srv = SRV(label = label, domain = domain,
                target=target, port=port, weight=weight,
                priority=prio)
            srv.full_clean()
            srv.save()
            if view:
                srv.views.add(view)
                srv.save()


    set_all_soas(base_domain, base_domain.soa)


def ensure_domain(name):
    parts = list(reversed(name.split('.')))
    domain_name = ''
    for i in range(len(parts)):
        domain_name = parts[i] + '.' + domain_name
        domain_name = domain_name.strip('.')
        clobber_objects = []  # Objects that have the same name as a domain
        # need to be deleted and then recreated
        try:
            mxs = MX.objects.filter(fqdn=domain_name)
            # It got here. It exists
            for mx in mxs:
                label = mx.label
                mxdomain = mx.domain
                server = mx.server
                prio = mx.priority
                ttl = mx.ttl
                mxviews = [view.name for view in mx.views.all()]
                mx.delete()
                mx = MX(label='', server=server, priority=prio, ttl=ttl)
                clobber_objects.append((mx, mxviews))
        except ObjectDoesNotExist, e:
            pass
        try:
            addrs = AddressRecord.objects.filter(fqdn=domain_name)
            for exists_a in addrs:
                # It got here. It exists
                need_to_recreate_a = True
                ip_str = exists_a.ip_str
                ip_type = exists_a.ip_type
                aviews = [view.name for view in exists_a.views.all()]
                exists_a.delete(check_cname=False)
                a = AddressRecord(label='', ip_str=ip_str, ip_type=ip_type)
                clobber_objects.append((a, aviews))
        except ObjectDoesNotExist, e:
            pass
        try:
            cname = CNAME.objects.get(fqdn=domain_name)
            # It got here. It exists
            data = cname.data
            cnviews = [view.name for view in cname.views.all()]
            cname.delete()
            cname = CNAME(label='', data=data)
            clobber_objects.append((cname, cnviews))
        except ObjectDoesNotExist, e:
            pass
        try:
            for txt in TXT.objects.filter(fqdn=domain_name):
                # It got here. It exists
                data = txt.txt_data
                txtviews = [view.name for view in txt.views.all()]
                txt.delete()
                txt = TXT(label='', txt_data=data)
                clobber_objects.append((txt, txtviews))
        except ObjectDoesNotExist, e:
            pass
        domain, created = Domain.objects.get_or_create(name=
                domain_name)
        for object_, views in clobber_objects:
            try:
                object_.domain = domain
                object_.clean()
                object_.save()
                for view_name in views:
                    view = View.objects.get(name=view_name)
                    object_.views.add(view)
                    object_.save()
            except ValidationError, e:
                # this is bad
                pdb.set_trace()
                pass

        if created and domain.master_domain and domain.master_domain.soa:
            #try:
            #    domain.save()
            #except ValidationError, e:
            #    pdb.set_trace()
            #    pass
            null_all_soas(domain)
            domain.soa = domain.master_domain.soa
            domain.save()
            set_all_soas(domain, domain.master_domain.soa)

    return domain


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
                dnsip = ip_to_domain_name(ip)
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
            dnsip = ip_to_domain_name(ip)
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
