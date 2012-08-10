from truth.models import Truth
from django.db import IntegrityError

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
from core.network.models import Network, NetworkKeyValue
from core.network.utils import calc_parent
from core.vlan.models import Vlan
from core.interface.static_intr.models import StaticInterface

import truth

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
from mozdns.view.models import View

import os.path
import pprint
import re
import ipaddr
import pdb

DEBUG = 3
DO_DEBUG = False

pp = pprint.PrettyPrinter(indent=2)

def migrate_networks():
    all = truth.models.Truth.objects.all()
    print all
    scopes = []
    for thing in all:
        if thing.name.find("-vlan") != -1:
            scopes.append(thing)
    vlan_number_re = re.compile("(\d+)$")
    is_network_start = re.compile("dhcp.scope.start")
    is_network_end = re.compile("dhcp.scope.end")
    is_netmask = re.compile("dhcp.scope.netmask")
    is_pool_start = re.compile("dhcp.pool.start")
    is_pool_end = re.compile("dhcp.pool.end")
    is_ntp_server = re.compile("dhcp.option.ntp_server.\d")
    is_domain_name = re.compile("dhcp.option.domain_name.\d")
    is_dns_servers = re.compile("dhcp.option.dns_server.\d")
    is_pool_allow_booting = re.compile("dhcp.pool.allow_booting.\d")
    is_pool_allow_bootp = re.compile("dhcp.pool.allow_bootp.\d")
    for scope in scopes:
        if str(scope).endswith("fake"):
            print "Skipping "+str(scope)
            continue
        vlan_number = vlan_number_re.search(str(scope)).groups(1)[0]
        network_start = None
        network_end = None
        netmask = None
        pool_start = None
        pool_end = None
        ntp_servers = []
        domain_name = None
        dns_servers = []
        allow_booting = None
        allow_bootp = None
        for kv in scope.keyvalue_set.all():
            if is_network_start.match(kv.key):
                network_start = kv.value
            if is_network_end.match(kv.key):
                network_end = kv.value
            if is_netmask.match(kv.key):
                netmask = kv.value
            if is_pool_start.match(kv.key):
                pool_start = kv.value
            if is_pool_end.match(kv.key):
                pool_end = kv.value
            if is_ntp_server.match(kv.key):
                ntp_servers.append(kv.value)
            if is_domain_name.match(kv.key):
                domain_name = kv.value
            if is_dns_servers.match(kv.key):
                dns_servers.append(kv.value)
            if is_pool_allow_booting.match(kv.key):
                allow_booting = bool(kv.value)
            if is_pool_allow_bootp.match(kv.key):
                allow_bootp = bool(kv.value)

        vlan = Vlan.objects.filter(number=vlan_number)
        try:
            net = ipaddr.IPv4Network(network_start+'/'+netmask)
        except ipaddr.AddressValueError, e:
            if str(scope) == "phx1-vlan75":
                net = ipaddr.IPv4Network("10.8.75.0/24")
            else:
                pdb.set_trace()
                continue
        network = Network.objects.filter(ip_lower=int(net.network),
                ip_upper = 0, prefixlen = net.prefixlen)

        print "="*20 + " " +str(scope)
        print "Expected Vlan: "+str(vlan)
        print vlan_number
        if not network:
            print "Creating new Network: "+str(net)
            network, _ = Network.objects.get_or_create(network_str = str(net), ip_type='4')
            parent = calc_parent(network)
            if parent:
                network.site = parent.site
        else:
            network = network[0]
            print "Existing Network: "+str(network)

        if vlan:
            network.vlan = vlan[0]
        else:
            v, _ = Vlan.objects.get_or_create(name="I need a name.", number=vlan_number)
            network.vlan = v
        network.save()

        print network_start
        print network_end
        print netmask
        print pool_start
        print pool_end
        print ntp_servers
        print domain_name
        print dns_servers
        print allow_booting
        print allow_bootp
        if str(scope) == "phx1-vlan75":
            continue
        if ntp_servers:
            real_ntp_servers = []
            for server in ntp_servers:
                if server == '':
                    continue
                else:
                    real_ntp_servers.append(server)
            if real_ntp_servers:
                kv = NetworkKeyValue(key="ntp-servers", value=", ".join(real_ntp_servers),
                        network=network)
                try:
                    kv.clean()
                    kv.save()
                except IntegrityError, e:
                    # Duplicate error
                    pass
        if domain_name:
            pdb.set_trace()
            kv = NetworkKeyValue(key="domain-name", value=domain_name,
                    network=network)
            try:
                kv.clean()
                kv.save()
            except IntegrityError, e:
                # Duplicate error
                pass
        if dns_servers:
            kv = NetworkKeyValue(key="ntp-servers", value=", ".join(dns_servers),
                    network=network)
            try:
                kv.clean()
                kv.save()
            except IntegrityError, e:
                # Duplicate error
                pass
        if allow_booting and not allow_bootp:
            kv = NetworkKeyValue(key="allow", value="booting", network=network)
            try:
                kv.clean()
                kv.save()
            except IntegrityError, e:
                # Duplicate error
                pass
        elif not allow_booting and allow_bootp:
            kv = NetworkKeyValue(key="allow", value="bootp", network=network)
            try:
                kv.clean()
                kv.save()
            except IntegrityError, e:
                # Duplicate error
                pass
        elif allow_booting and allow_bootp:
            kv = NetworkKeyValue(key="allow", value="booting, bootp",
                    network=network)
            try:
                kv.clean()
                kv.save()
            except IntegrityError, e:
                # Duplicate error
                pass
