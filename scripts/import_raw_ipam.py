__import__('inventory_context')
import sys

from core.site.models import Site
from core.vlan.models import Vlan
from core.network.models import Network, NetworkKeyValue


def ensure_site(site_name):
    for s in reversed(site_name.split('.')):
        site, _ = Site.objects.get_or_create(full_name=s)
    return site


def ensure_vlan(vlan_number, vlan_name):
    if not (vlan_number and vlan_name):
        return None
    v, _ = Vlan.objects.get_or_create(number=vlan_number, name=vlan_name)
    return v


def ensure_network(site, vlan, network_str, sec_zone):
    ip_type = '6' if network_str.find('.') == -1 else '4'
    if ip_type == '4':
        network_addr, mask = network_str.split('/')
        octets = network_addr.split('.')
        while len(octets) != 4:
            octets.append('0')
        network_str = '.'.join(octets) + '/' + mask

    n, _ = Network.objects.get_or_create(
        network_str=network_str, ip_type=ip_type
    )
    n.vlan = vlan
    n.site = site
    n.save() if vlan or site else 0
    return n


with open(sys.argv[1], 'r') as fd:
    for line in fd.readlines()[1:]:
        (site_name, vlan_number, sec_zone, vlan_name,
            network_str) = line.strip('\n').split(',')
        print '========================================='
        print ("site_name: '{0}'\n"
               "vlan_number: '{1}'\n"
               "security_zone: '{2}'\n"
               "vlan_name: '{3}'\n"
               "vlan_number: '{4}'\n"
               "network_str: '{5}'").format(site_name, vlan_number, sec_zone,
                                            vlan_name, vlan_number,
                                            network_str)
        site = ensure_site(site_name)
        vlan = ensure_vlan(vlan_number, vlan_name)
        network = ensure_network(site, vlan, network_str, sec_zone)
        NetworkKeyValue.objects.get_or_create(
            key='security_zone', value=sec_zone, obj=network
        )
