from django.core.exceptions import ObjectDoesNotExist, ValidationError

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
from mozdns.utils import ensure_domain

from settings import ZONE_PATH

from mdns.svn_build import collect_svn_zone, collect_rev_svn_zone

import dns
import dns.zone
import pdb
from copy import deepcopy

def buildzone3(job):
    if job == "external":
        from mdns.migrate.zone_configs.external import external
        configs = external
    if job == "private_reverse":
        from mdns.migrate.zone_configs.private_reverse import private_reverse
        configs = private_reverse
    if job == "net":
        from mdns.migrate.zone_configs.mozilla_net import mozilla_net
        configs = mozilla_net
    if job == "org":
        from mdns.migrate.zone_configs.mozilla_org import mozilla_org
        configs = mozilla_org
    if job == "com":
        from mdns.migrate.zone_configs.mozilla_com_dc_zone_config import mozilla_com_dcs
        configs = mozilla_com_dcs
    build_from_config(configs)

def build_from_config(configs):
    for config in configs:
        zone_path = config['path']
        root_domain_name = config['zone_name']
        name_reversed = config['name_reversed']
        ztype = config['direction']
        view = config['view']
        relative_path = config['relative_path']
        migrate_zone(root_domain_name, name_reversed, zone_path, ztype, view, relative_path)


def migrate_zone(root_domain_name, name_reversed, zone_path, ztype, view, relative_path):
    if view == "both":
        private , _ = View.objects.get_or_create(name="private")
        public , _ = View.objects.get_or_create(name="public")
        views = [private, public]
    else:
        view_obj, _ = View.objects.get_or_create(name=view)
        views = [view_obj]

    try:
        if ztype == 'r':
            if name_reversed:
                root_domain_name = '.'.join(reversed(root_domain_name.split('.'))
                        ) + ".in-addr.arpa"
            else:
                root_domain_name = '.'.join(root_domain_name.split('.')) + ".in-addr.arpa"
        svn_zone = collect_svn_zone(root_domain_name, zone_path, ZONE_PATH)
    except dns.zone.NoSOA, e:
        print "----------------------"
        print "ERROR: NoSOA()"
        print zone_path
        print "----------------------"
        return
    if ztype == 'f':
        print "++ Migrating {0} {1}".format(root_domain_name, zone_path)
        populate_forward_dns(svn_zone, root_domain_name, views)
    if ztype == 'r':
        print "++ Migrating {0} {1}".format(root_domain_name, zone_path)
        populate_reverse_dns(svn_zone, name_reversed, root_domain_name, views)

def null_zone_tree(domain, clobber_soa):
    """Starting at domain, change any domain's soa that is clobber_soa to None.
    """
    if domain.soa is None:
        pass  # Keep searching (even though you won't find anything)
    elif domain.soa == clobber_soa:
        pass  # Kill it with fire!
    elif domain.soa != clobber_soa:
        return  # We hit a new zone. Leave if alone
    else:
        # Oh fuck
        pdb.set_trace()
        pass
    # Let's go deeper. (TWSS)
    for child_domain in domain.domain_set.all():
        null_zone_tree(child_domain, clobber_soa)
    domain.soa = None
    domain.save()
    return


def color_zone_tree(domain, clobber_soa, new_soa):
    """
    This function will take the domain tree and give domain's their 'assumed'
    correct soa. This is an in order traversal.
    """

    if domain.soa == clobber_soa:
        pass  # We are changing this soa
    elif domain.soa == new_soa:
        pass  # We still need to check the child domains
    elif domain.soa is None and not domain.delegated:
        pass  # This domain doesn't have an soa and isn't delegated. It's
              # likely it was just created. Set it's SOA.
    elif domain.soa != clobber_soa and domain.soa is not None:
        return  # It's a different zone. We've arrived at our base case.
    else:
        # Oh fuck
        pdb.set_trace()
        pass

    domain.soa = new_soa
    domain.save()
    # Let's go deeper. (TWSS)
    for child_domain in domain.domain_set.all():
        color_zone_tree(child_domain, clobber_soa, new_soa)
    return

def populate_forward_dns(zone, root_domain_name, views):
    soa = migrate_soa(zone, root_domain_name)
    root_domain = ensure_domain(root_domain_name, force=True)
    migrate_A(zone, root_domain, soa, views)
    migrate_AAAA(zone, root_domain, soa, views)
    migrate_NS(zone, root_domain, soa, views)
    migrate_CNAME(zone, root_domain, soa, views)
    migrate_MX(zone, root_domain, soa, views)
    migrate_TXT(zone, root_domain, soa, views)
    migrate_SRV(zone, root_domain, soa, views)
    if root_domain.soa == soa:
        clobber_soa = None
    else:
        clobber_soa = root_domain.soa
    null_zone_tree(root_domain, clobber_soa)
    color_zone_tree(root_domain, clobber_soa, soa)


def populate_reverse_dns(zone, name_reversed, root_domain_name, views):
    ensure_domain("arpa", force=True)
    ensure_domain("in-addr.arpa", force=True)
    ensure_domain("ipv6.arpa", force=True)
    soa = migrate_soa(zone, root_domain_name)
    root_domain = ensure_domain(root_domain_name, force=True)
    migrate_NS(zone, root_domain, soa, views)
    migrate_MX(zone, root_domain, soa, views)
    migrate_PTR(zone, root_domain, soa, views)
    if root_domain.soa == soa:
        clobber_soa = None
    else:
        clobber_soa = root_domain.soa
    null_zone_tree(root_domain, clobber_soa)
    color_zone_tree(root_domain, root_domain.soa, soa)

def migrate_PTR(zone, root_domain, soa, views):
    for (name, ttl, rdata) in zone.iterate_rdatas('PTR'):
        fqdn = rdata.target.to_text().strip('.')
        if fqdn.find('unused') != -1:
            print "Skipping "+name.to_text()+" "+fqdn
            continue

        # 4.3.2.1.IN-ADDR.ARPA. --> 1.2.3.4
        name = name.to_text().lower().strip('.')
        if name.endswith('.in-addr.arpa'):
            ip_type = '4'
            ip_str = name.replace('.in-addr.arpa','')
        elif name.endswith('.ipv6.arpa'):
            ip_type = '6'
            ip_str = name.replace('.ipv6.arpa','')
            raise NotImplemented("Ipv6 migration isn't done yet.")
        else:
            print "We so fucked. Lol"
            pdb.set_trace()
            continue

        ip_str = '.'.join(list(reversed(ip_str.split('.'))))
        if ip_str == '10.2.171.IN':
            print "Skipping "+ip_str+" "+fqdn
            continue

        print str(name) + " PTR " + str(fqdn)
        ptr = PTR.objects.filter(name = fqdn, ip_str = ip_str, ip_type='4')
        if ptr:
            ptr = ptr[0]
        else:
            ptr = PTR(name = fqdn, ip_str = ip_str, ip_type='4')
            ptr.full_clean()
            ptr.save()

        if views:
            for view in views:
                ptr.views.add(view)



def migrate_soa(zone, root_domain_name):
    for (name, ttl, rdata) in zone.iterate_rdatas('SOA'):
        print str(name) + " SOA " + str(rdata)
        exists = SOA.objects.filter(minimum=rdata.minimum,
                contact=rdata.rname.to_text().strip('.'),
                primary=rdata.mname.to_text().strip('.'), comment="SOA for"
                " {0}".format(root_domain_name))
        if exists:
            soa = exists[0]
        else:
            soa = SOA(serial=rdata.serial, minimum=rdata.minimum,
                    contact=rdata.rname.to_text().strip('.'),
                    primary=rdata.mname.to_text().strip('.'), comment="SOA for"
                    " {0}".format(root_domain_name))
            soa.clean()
            soa.save()
    return soa

def migrate_A(zone, root_domain, soa, views):
    names = []
    for (name, ttl, rdata) in zone.iterate_rdatas('A'):
        names.append((name.to_text().strip('.'), rdata))
    sorted_names = list(sorted(names, cmp=lambda n1, n2: -1 if
        len(n1[0].split('.'))> len(n2[0].split('.')) else 1))

    for name, rdata in sorted_names:
        print str(name) + " A " + str(rdata)
        if name.startswith("unusedspace"):
            print "Skipping {0} A {1}".format(name, rdata)
            continue
        exists_domain =  Domain.objects.filter(name=name)
        if exists_domain:
            label = ''
            domain = exists_domain[0]
        else:
            label = name.split('.')[0]
            domain_name = '.'.join(name.split('.')[1:])
            domain = ensure_domain(domain_name, force=True)
        a, _ = AddressRecord.objects.get_or_create(label=label,
                domain=domain, ip_str=rdata.to_text(), ip_type='4')
        for view in views:
            a.views.add(view)
            a.save()

def migrate_AAAA(zone, root_domain, soa, views):
    for (name, ttl, rdata) in zone.iterate_rdatas('AAAA'):
        name = name.to_text().strip('.')
        print str(name) + " AAAA " + str(rdata)
        exists_domain =  Domain.objects.filter(name=name)
        if exists_domain:
            label = ''
            domain = exists_domain[0]
        else:
            label = name.split('.')[0]
            if label.startswith('unused'):
                continue
            domain_name = '.'.join(name.split('.')[1:])
            domain = ensure_domain(domain_name, force=True)

        ip_upper, ip_lower = ipv6_to_longs(rdata.to_text())
        if AddressRecord.objects.filter(label=label,
                domain=domain, ip_upper=ip_upper, ip_lower=ip_lower,
                ip_type='6').exists():
            a = AddressRecord.objects.get(label=label,
                    domain=domain, ip_type='6', ip_upper=ip_upper,
                    ip_lower=ip_lower)
        else:
            a = AddressRecord(label=label, domain=domain,
                    ip_str=rdata.to_text(), ip_type='6')
            a.clean()
            a.save()
        for view in views:
            a.views.add(view)
            a.save()

def migrate_NS(zone, root_domain, soa, views):
    for (name, ttl, rdata) in zone.iterate_rdatas('NS'):
        name = name.to_text().strip('.')
        print str(name) + " NS " + str(rdata)
        domain_name = '.'.join(name.split('.')[1:])
        domain = ensure_domain(name, force=True)
        ns, _ = Nameserver.objects.get_or_create(domain=domain,
                server=rdata.target.to_text().strip('.'))
        for view in views:
            ns.views.add(view)
            ns.save()

def migrate_MX(zone, root_domain, soa, views):
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
            domain = ensure_domain(domain_name, force=True)
        priority = rdata.preference
        server = rdata.exchange.to_text().strip('.')
        mx, _ = MX.objects.get_or_create(label=label, domain=domain,
                server= server, priority=priority, ttl="3600")
        for view in views:
            mx.views.add(view)
            mx.save()


def migrate_CNAME(zone, root_domain, soa, views):
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
            domain = ensure_domain('.'.join(domain_name), force=True)
        data = rdata.target.to_text().strip('.')

        if not CNAME.objects.filter(label = label, domain = domain,
                target = data).exists():
            cn = CNAME(label = label, domain = domain, target = data)
            cn.full_clean()
            cn.save()
            for view in views:
                cn.views.add(view)
                cn.save()


def migrate_TXT(zone, root_domain, soa, views):
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
            domain = ensure_domain('.'.join(domain_name), force=True)
        data = rdata.to_text().strip('"')

        if not TXT.objects.filter(label = label, domain = domain,
                txt_data = data).exists():
            txt = TXT(label = label, domain = domain, txt_data = data)
            txt.full_clean()
            txt.save()
            for view in views:
                txt.views.add(view)
                txt.save()


def migrate_SRV(zone, root_domain, soa, views):
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
            domain = ensure_domain('.'.join(domain_name), force=True)

        if not SRV.objects.filter(label = label, domain = domain,
                target=target, port=port, weight=weight,
                priority=prio).exists():
            srv = SRV(label = label, domain = domain,
                target=target, port=port, weight=weight,
                priority=prio)
            srv.full_clean()
            srv.save()
            for view in views:
                srv.views.add(view)
                srv.save()

def get_clobbered(domain_name):
    classes = [MX, AddressRecord, CNAME, TXT, SRV]
    clobber_objects = []  # Objects that have the same name as a domain
    for Klass in classes:
        objs = Klass.objects.filter(fqdn=domain_name)
        for obj in objs:
            obj_views = [view.name for view in obj.views.all()]
            new_obj = deepcopy(obj)
            new_obj.id = None
            clobber_objects.append((new_obj, obj_views))
            if Klass == AddressRecord:
                kwargs = {"check_cname": False}
            else:
                kwargs = {}
            obj.delete(**kwargs)
    return clobber_objects

"""
def ensure_domain(name):
    try:
        domain = Domain.objects.get(name=name)
        return domain
    except ObjectDoesNotExist, e:
        pass
    parts = list(reversed(name.split('.')))
    domain_name = ''
    for i in range(len(parts)):
        domain_name = parts[i] + '.' + domain_name
        domain_name = domain_name.strip('.')
        clobber_objects = get_clobbered(domain_name)
        # need to be deleted and then recreated
        domain, created = Domain.objects.get_or_create(name=domain_name)
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
    return domain
"""
