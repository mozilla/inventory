from core.network.models import Network

def get_networks(site):
    """
    n(S^i) - All networks that are in a site.
    """
    nets = []
    for network in Network.objects.all():
        if site in network.sites.all():
            nets.append(network)
    return nets

def get_vlans(site):
    """
    v(S^i) = {N^i^v | N^i e n(S^i)}
    returns a set
    """
    vlans = set()
    networks = get_networks(site)
    for network in networks:
        if network.vlan:
            vlans.add(network.vlan)
    return vlans
