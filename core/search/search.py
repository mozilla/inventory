from django.db.models import Q
from core.network.utils import calc_parent
from django.core.exceptions import ObjectDoesNotExist, ValidationError

import mozdns
import core
import operator
from core.network.models import Network
from core.site.models import Site
from core.vlan.models import Vlan

import pdb


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
    for network in vlan.network_set.all():
        queries, n_misc = nif(network, root=False)
        range_queries += queries
        misc.update(n_misc)
        if root:
            misc.add(network)
    return [reduce(operator.or_, range_queries)], misc


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
    network.update_network()
    return [ipf(int(network.network.network), int(network.network.broadcast),
        root=False)], misc


def ipf(start, end, root=True):
    """
    Get all objects within start and end. Start and end *could* be numbers
    larger than 64 bits.
    """
    start_upper = start >> 64
    start_lower = start & (1 << 64) - 1
    end_upper = end >> 64
    end_lower = end & (1 << 64) - 1

    #query = Q(ip_upper__lte=start_upper, ip_upper__gte=end_upper)
    query = Q(ip_upper=start_upper, ip_lower__gte=start_lower,
            ip_lower__lte=end_lower)
    return query

def build_filter(f, fields, filter_type = "icontains"):
    filter_ = {}
    # rtucker++
    filters =[Q(**{"{0}__{1}".format(t, filter_type): f}) for t in fields]
    # Breaks in python 3. Oh well
    return reduce(operator.or_, filters)


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

    # IP Filters
    misc = set()
    range_queries = []
    for site_str in site_fs:
        try:
            site = Site.objects.get(name=site_str)
        except ObjectDoesNotExist, e:
            continue
        queries, s_misc = sif(site)
        range_queries += queries
        misc = misc.union(s_misc)

    for network_str in network_fs:
        try:
            # Guess which network type they are searching by looking for ':'
            if network_str.find(':') > -1:
                network = ipaddr.IPv6Address(network_str=network_str, ip_type='6')
                network.update_network()
            else:
                network = Network(network_str=network_str, ip_type='4')
                network.update_network()
        except ValidationError, e:
            continue
        except ipaddr.AddressValueError, e:
            continue
        queries, n_misc = nif(network)
        range_queries += queries
        misc = misc.union(n_misc)

    for vlan_str in vlan_fs:
        try:
            vlan = Vlan.objects.get(name=vlan_str)
        except ObjectDoesNotExist, e:
            try:
                vlan = Vlan.objects.get(number=vlan_str)
            except ObjectDoesNotExist, e:
                continue
        queries, v_misc = vif(vlan)
        range_queries += queries
        misc = misc.union(v_misc)

    if range_queries:
        # We need to AND all of these Q set's together.
        mega_filter = tuple(range_queries)
        AddressRecord = mozdns.address_record.models.AddressRecord
        addrs = AddressRecord.objects.filter(*mega_filter).order_by('ip_upper').order_by('ip_lower')
        cnames = None
        domains = None
        StaticInterface = core.interface.static_intr.models.StaticInterface
        intrs = StaticInterface.objects.filter(*mega_filter)
        mxs = None
        nss = None
        PTR = mozdns.ptr.models.PTR
        ptrs = PTR.objects.filter(*mega_filter)
        srvs = None
        txts = None
    else:
        AddressRecord = mozdns.address_record.models.AddressRecord
        addrs = AddressRecord.objects.all()

        CNAME = mozdns.cname.models.CNAME
        cnames = CNAME.objects.all()

        Domain = mozdns.domain.models.Domain
        domains = Domain.objects.all()

        StaticInterface = core.interface.static_intr.models.StaticInterface
        intrs = StaticInterface.objects.all()

        MX = mozdns.mx.models.MX
        mxs = MX.objects.all()

        Nameserver = mozdns.nameserver.models.Nameserver
        nss = Nameserver.objects.all()

        PTR = mozdns.ptr.models.PTR
        ptrs = PTR.objects.all()

        SRV = mozdns.srv.models.SRV
        srvs = SRV.objects.all()

        TXT = mozdns.txt.models.TXT
        txts = TXT.objects.all()

    # NAME FILTER
    for f in text_fs:
        if addrs:
            addr_filter = build_filter(f, AddressRecord.search_fields)
            addrs = addrs.filter(addr_filter)
    """
        if cnames:
            cnames = cnames.filter(f)
        if domains:
            domains = domains.filter(f)
        if intrs:
            intrs = intrs.filter(f)
        if mxs:
            mxs = mxs.filter(f)
        if nss:
            nss = nss.filter(f)
        if ptrs:
            ptrs = ptrs.filter(f)
        if srvs:
            srvs = srvs.filter(f)
        if txts:
            txts = txts.filter(f)
    """
    cnames = None
    domains = None
    intrs = None
    mxs = None
    nss = None
    ptrs = None
    srvs = None
    txts = None

    # TODO

    return addrs, cnames, domains, intrs, mxs, nss, ptrs, srvs, txts, misc


