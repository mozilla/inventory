from django.db.models import Q
from core.network.utils import calc_parent


def sif(site):
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
    # Return list to make consistent with vif
    parent_net.update_network()
    return [ipf(int(parent_net.network.network),
        int(parent_net.network.broadcast), root=False)], misc


def vif(vlan, root=True):
    if not vlan:
        return [], None
    misc = set()
    if root:
        misc.add(vlan)
    range_queries = []
    for network in v.net_set.all():
        range_queries += nif(network, root=False)
    return range_queries, misc


def nif(network, root=True):
    if not network:
        return [], None
    misc = set()
    misc = set()
    if root:
        misc.add(network)
        if network.vlan:
            misc.add(network.vlan)
    if network.site:
        misc.add(network.site)
    # Return list to make consistent with vif
    networ.update_network()
    return [ipf(int(network.network.network), int(network.network.broadcast),
        root=False)], misc


def ipf(start, end, root=True):
    """
    Get all objects within start and end. Start and end *could* be numbers
    larger than 64 bits.
    """
    start_upper = start >> 64
    start_lower = start & (1 << 64) - 1
    end_upper = start >> 64
    end_lower = start & (1 << 64) - 1

    query = Q(ip_upper__gte=start_upper, ip_upper__lte=end_upper)
    query = query | Q(ip_upper=start_upper, ip_lower__gte=start_lower,
            ip_lower__lte=end_lower)
    return query

def compile_search(args):
    """
    This function needs to look at all the args and aggrigate the results.
    If There is an IP search it will do an IP Filter (ipf) and pass the
    resulting Q set's to the Name Filter (nf). If there is not ipf then all
    objects are subjected to a nf.
    """
    text_fs = []
    n_text_fs = []

    site_fs = []
    n_site_fs = []

    network_fs = []
    n_network_fs = []

    vlan_fs = []
    n_vlan_fs = []

    range_fs = []
    n_range_fs = []

    for arg in args:
        if arg[1] == "text:":
            if arg[0] == "inc":
                text_fs += arg[2]
            if arg[0] == "exc":
                n_text_fs += arg[2]
        elif arg[1] == "site:":
            if arg[0] == "inc":
                site_fs += arg[2]
            if arg[0] == "exc":
                n_site_fs += arg[2]
        elif arg[1] == "vlan:":
            if arg[0] == "inc":
                vlan_fs += arg[2]
            if arg[0] == "exc":
                n_vlan_fs += arg[2]
        elif arg[1] == "network:":
            if arg[0] == "inc":
                network_fs += arg[2]
            if arg[0] == "exc":
                n_network_fs += arg[2]
        elif arg[1] == "range:":
            if arg[0] == "inc":
                range_fs += arg[2]
            if arg[0] == "exc":
                n_range_fs += arg[2]

    text_fs = list(set(text_fs))
    n_text_fs = list(set(n_text_fs))

    site_fs = list(set(site_fs))
    n_site_fs = list(set(n_site_fs))

    network_fs = list(set(network_fs))
    n_network_fs = list(set(n_network_fs))

    vlan_fs = list(set(vlan_fs))
    n_vlan_fs = list(set(n_vlan_fs))

    range_fs = list(set(range_fs))
    n_range_fs = list(set(n_range_fs))

    misc = set()
    range_queries = []
    for site in site_fs:
        queries, misc = sif(site)
        range_queries += queries
        misc.union(misc)

    for network in network_fs:
        queries, misc = nif(network)
        range_queries += queries
        misc.union(misc)

    for vlan in vlan_fs:
        queries, misc = sif(vlan)
        range_queries += queries
        misc.union(misc)

    if range_queries:
        mega_filter = Q()
        # We need to AND all of these Q set's together.
        mega_filter = tuple(range_queries)
        addrs = AddressRecord.objects.filter(*mega_filter)
        cnames = None
        domains = None
        intrs = StaticInterface.objects.filter(*mega_filter)
        mxs = None
        nss = None
        ptrs = PTR.objects.filter(*mega_filter)
        srvs = None
        txts = None

    # NAME FILTER
    # TODO

    return addrs, cnames, domains, intrs, mxs, nss, ptrs, srvs, txts, misc


