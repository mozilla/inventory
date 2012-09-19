from django.db.models import Q
from core.network.utils import calc_parent
from django.core.exceptions import ObjectDoesNotExist, ValidationError

import mozdns
import core
import operator
from core.network.models import Network
from core.site.models import Site
from core.vlan.models import Vlan
from core.utils import IPFilterSet

import pdb
import ipaddr


"""
Compile a search into a list of tubles in the format:
    (start_upper, start_lower, end_upper, end_lower, proto)

start_upper, start_lower - int with 64bits of info
end_upper, end_lower - int with 64bits of info
proto - Either '4' or '6'
"""

def sif(ipfset, site):
    if not site:
        return [], None
    misc = set()
    networks = site.network_set.all()
    if not networks:
        return None
    parent_net = calc_parent(networks[0])
    if not parent_net:
        parent_net = networks[0]
    misc.add(site)
    misc.add(parent_net)
    parent_net.update_ipf()
    ipfset.add(parent_net.ipf)
    return ipfset, misc


def vif(ipfset, vlan, root=True):
    if not vlan:
        return ipfset, None
    misc = set()
    if root:
        misc.add(vlan)
    for network in vlan.network_set.all():
        network.update_ipf()
        ipfset.add(network.ipf)
        misc.add(network)
        if root:
            misc.add(network)
    return ipfset, misc


def nif(ipfset, network, root=True):
    if not network:
        return [], None
    misc = set()
    misc = set()
    if root:
        try:
            n = Network.objects.get(ip_upper=network.ip_upper,
                    ip_lower=network.ip_lower, ip_type=network.ip_type,
                    prefixlen=network.prefixlen)
            misc.add(n)
        except ObjectDoesNotExist, e:
            pass
        if network.vlan:
            misc.add(network.vlan)
    if network.site:
        misc.add(network.site)
    # Return list to make consistent with vif
    network.update_ipf()
    ipfset.add(network.ipf)
    return ipfset, misc


def ipf(ipfset, start, end, ip_type, root=True):
    """
    Get all objects within start and end. Start and end *could* be numbers
    larger than 64 bits.
    """
    x = two_to_four(start, end)
    start_upper, start_lower, end_upper, end_lower = x
    start_upper = start_upper
    start_lower = start_lower
    end_upper = end_upper
    end_lower = end_lower
    ip_type = ip_type
    try:
        range_ = Range.objects.get(start_upper=start_upper,
                    start_lower=start_lower, end_upper=end_upper,
                    end_lower=end_lower, ip_type=ip_type)
    except ObjectDoesNotExist, e:
        range_ = None
    ipf = IPFilter(range_, ip_type, start_upper, start_lower, end_upper,
            end_lower)
    ipfset.add(ipf)
    return ipfset

def run_test():
    ipfset = IPFilterSet()
    print sif(ipfset, Site.objects.get(name='scl3'))
    print vif(ipfset, Vlan.objects.get(name='private'))
    print '-'*8
    ipfset.pprint()
