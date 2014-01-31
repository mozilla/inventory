from core.network.models import Network


def calc_networks(network, nq=None):
    network.update_network()
    eldars = []
    sub_networks = []
    if not nq:
        nq = Network.objects.all()

    for pnet in nq.order_by('prefixlen', 'ip_upper', 'ip_lower'):
        pnet.update_network()
        if pnet.pk == network.pk:
            continue
        if pnet.network.overlaps(network.network):
            if pnet.prefixlen > network.prefixlen:
                sub_networks.append(pnet)
            else:
                eldars.append(pnet)

    return eldars, sub_networks


def calc_parent(network):
    eldars, sub_net = calc_networks(network)
    if not eldars:
        return []
    parent = list(reversed(sorted(eldars, key=lambda n: n.prefixlen)))[0]
    return parent


def calc_parent_str(network_str, ip_type):
    network = Network(network_str=network_str, ip_type=ip_type)
    return calc_parent(network)


def calc_networks_str(network_str, ip_type):
    network = Network(network_str=network_str, ip_type=ip_type)
    return calc_networks(network)


def calc_top_level_networks(site):
    networks = list(
        site.network_set.order_by('prefixlen', 'ip_upper', 'ip_lower')
    )
    nq = Network.objects.filter(site=site)
    tlns = []
    while True:
        try:
            cur = networks.pop(0)
        except IndexError:
            break

        super_nets, sub_nets = calc_networks(cur, nq=nq)
        if not super_nets:
            tlns.append(cur)

        for sn in sub_nets:
            try:
                networks.remove(sn)
            except ValueError:
                pass  # The network might have a different site

    def ncmp(n1, n2):
        pd = n1.prefixlen - n2.prefixlen
        if pd != 0:
            return pd
        n_u_d = n1.ip_upper - n2.ip_upper
        if n_u_d != 0:
            return n_u_d
        return n1.ip_lower - n2.ip_lower

    #return sorted(tlns, cmp=lambda n1, n2: int(ncmp(n1, n2) % 2))
    return tlns
