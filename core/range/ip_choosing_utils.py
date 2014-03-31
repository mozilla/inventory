from django.db.models import Q
from django.shortcuts import get_object_or_404
from core.site.models import Site
from core.vlan.models import Vlan
from core.network.models import Network
from core.utils import overlap, ip_to_int


def pks_to_objs(pks, Klass):
    return map(lambda pk: get_object_or_404(Klass, pk=pk), pks)


# Only certain networks should be displayed to users for allocating into.
# * For ipv4, only networks with a netmask larger than or equal to 20
#   should be displayed
# * For ipv6, only /64 networks should be displayed
UN = (  # user networks
    (Q(ip_type='4') & Q(prefixlen__gte=20)) |
    (Q(ip_type='6') & Q(prefixlen=64))
)


def calculate_filters(choice_type, choice_pk):
    """
    Write three functions that given a list of present primary keys
    ('present_pks') that are in the UI will remove the correct pk's and
    return a list of raised objects.

    filter_network will return a list of Networks
    filter_site will return a list of Sites
    filter_vlan will return a list of Vlans

    The 'present_pks' value is a list of integers that represent primary
    keys of the type of objects the function returns.
    """

    if choice_type == 'network':
        network = get_object_or_404(Network, pk=choice_pk)

        def filter_network(present_pks):
            return [network]

        def filter_site(present_pks):
            return [network.site] if network.site else []

        def filter_vlan(present_pks):
            return [network.vlan] if network.vlan else []

    elif choice_type == 'site':
        def filter_network(present_pks):
            """
            Remove any present network pk's that aren't in the network
            """
            site_network_pks = get_object_or_404(
                Site, pk=choice_pk
            ).network_set.filter(UN).values_list('pk', flat=True)
            net_pks = set(present_pks).intersection(set(site_network_pks))
            return pks_to_objs(net_pks, Network)

        def filter_site(present_pks):
            return [get_object_or_404(Site, pk=choice_pk)]

        def filter_vlan(present_pks):
            vlans = pks_to_objs(present_pks, Vlan)

            def is_in_site(vlan):
                return vlan.network_set.filter(
                    site__pk=choice_pk).filter(UN).exists()

            return filter(is_in_site, vlans)

    elif choice_type == 'vlan':
        vlan = get_object_or_404(Vlan, pk=choice_pk)

        def filter_network(present_pks):
            net_pks = vlan.network_set.filter(UN).values_list('pk', flat=True)
            net_pks = set(present_pks).intersection(set(net_pks))
            return pks_to_objs(net_pks, Network)

        def filter_site(present_pks):
            networks = vlan.network_set.filter(UN).filter(~Q(site=None))
            network_site_pks = networks.values_list('site', flat=True)
            site_pks = set(present_pks).intersection(set(network_site_pks))
            return pks_to_objs(site_pks, Site)

        def filter_vlan(present_pks):
            return [vlan]

    else:
        raise Exception("Not sure what to do here...")

    return filter_network, filter_site, filter_vlan


def label_value_maker():
    """
    We are going to need to put vlans, sites, networks, and ranges into the
    dom. This function makes functions that can make lists of JSON-able
    objects.
    """

    def format_network(networks):
        return list(
            {'label': n.network_str, 'value': n.pk} for n in networks
        )

    def format_site(sites):
        return list(
            {'label': s.full_name, 'value': s.pk} for s in sites
        )

    def format_vlan(vlans):
        return list(
            {'label': "{0}:{1}".format(v.name, v.number), 'value': v.pk}
            for v in vlans
        )
    return format_network, format_site, format_vlan


def calc_template_ranges(network):
    """
    Given a network, return the range information for that network. These
    ranges will be used by the user to decide where to request an IP address.
    This function will not actually find that ip address, it will mearly
    suggest which ranges a user might want to check in.

    This function should contain allocation policy that netops controls.
    """
    # See https://mana.mozilla.org/wiki/display/NOC/Node+deployment for
    # allocation templates

    network.update_network()
    dhcp_scope = network.calc_dhcp_scope_name()
    nbase = network.network.network
    name_fragment = calc_name_fragment(network)

    if network.ip_type == '4':
        # if it's in between a /24 or and /20 use this template
        if network.prefixlen <= 24 and network.prefixlen >= 20:
            template_ranges = [
                {
                    'name': 'template',
                    'rtype': 'special purpose',
                    'start': str(nbase + 1),
                    'end': str(nbase + 15),
                    'dhcp_scope': dhcp_scope,
                    'name_fragment': name_fragment
                },
                {
                    'name': 'template',
                    'rtype': 'multi-host pools',
                    'start': str(nbase + 16),
                    'end': str(nbase + 127),
                    'dhcp_scope': dhcp_scope,
                    'name_fragment': name_fragment
                },
                {
                    'name': 'template',
                    'rtype': '/32 allocations',
                    'start': str(nbase + 128),
                    'end': str(nbase + 207),
                    'dhcp_scope': dhcp_scope,
                    'name_fragment': name_fragment
                },
                {
                    'name': 'template',
                    'rtype': 'load balancers',
                    'start': str(nbase + 208),
                    'end': str(nbase + 223),
                    'dhcp_scope': dhcp_scope,
                    'name_fragment': name_fragment
                },
                {
                    'name': 'template',
                    'rtype': 'dynamic',
                    'start': str(nbase + 224),
                    'end': str(nbase + 247),
                    'dhcp_scope': dhcp_scope,
                    'name_fragment': name_fragment
                },
                {
                    'name': 'template',
                    'rtype': 'reserved',
                    'start': str(nbase + 248),
                    'end': str(nbase + 255),
                    'dhcp_scope': dhcp_scope,
                    'name_fragment': name_fragment
                }
            ]
            if network.prefixlen < 24:
                template_ranges.append({
                    'name': 'template',
                    'rtype': 'general purpose',
                    'start': str(nbase + 256),
                    'end': str(network.network.broadcast - 1),
                    'dhcp_scope': dhcp_scope,
                    'name_fragment': name_fragment
                })
        elif network.prefixlen > 24 and network.prefixlen < 31:
            # for subnets smaller than /24, reserve first /30
            template_ranges = [{
                'name': 'template',
                'rtype': 'reserved',
                'start': str(nbase + 0),
                'end': str(nbase + 3),
                'dhcp_scope': dhcp_scope,
                'name_fragment': name_fragment
            }]

            if network.prefixlen > 30:
                template_ranges.append({
                    'name': 'template',
                    'rtype': 'general purpose',
                    'start': str(nbase + 5),
                    'end': str(network.network.broadcast - 1),
                    'dhcp_scope': dhcp_scope,
                    'name_fragment': name_fragment
                })
        else:
            template_ranges = []
        return template_ranges
    elif network.ip_type == '6' and network.prefixlen == 64:
        # Only do /64s for IPv6
        # reserve the first /112 for human created IPs, the rest is unallocated
        # in the /64

        # /112 is the first :ffff addresses
        return [
            {
                'name': 'template',
                'rtype': 'reserved (netops)',
                'start': str(nbase + 1),
                'end': str(nbase + int('ffff', 16)),
                'dhcp_scope': dhcp_scope,
                'name_fragment': name_fragment
            },
            {
                'name': 'template',
                'rtype': 'general purpose',
                'start': str(nbase + int('10001', 16)),
                'end': str(nbase + int('1ffff', 16)),
                'dhcp_scope': dhcp_scope,
                'name_fragment': name_fragment
            },
            {
                'name': 'template',
                'rtype': 'vips',
                'start': str(nbase + int('20001', 16)),
                'end': str(nbase + int('2ffff', 16)),
                'dhcp_scope': dhcp_scope,
                'name_fragment': name_fragment
            }
        ]
    else:
        return []


def integrate_real_ranges(network, template_ranges):
    """
    Say we have a network::

        10.8.0.0                                                     10.8.0.255
        |------------------------------------------------------....--|


    For every network there is (or should be) a range template. This breaks up
    the range into reservations that the user can then select from when finding
    a free ip address::

        10.8.0.0                                                     10.8.0.255
        |------------------------------------------------------....--|
         |--template--|             |------template-----|
         10.8.0.1     10.8.0.10     10.8.0.50           10.8.0.100


    "Template" ranges are not real objects in the database; they do not have
    detail pages, they do not show up in search, and they do not have primary
    keys. They are a simple *default* overlay onto a network's ip space.

    There is, however, a real version of a range that is stored in Inventory's
    database; it has a detail page, shows up in searches, and has a primary
    key. These range objects have a ``start`` and ``end`` ip address and have a
    foreign key back to a specific Inventory network object. They serve the
    same purpose as a template range except they are defined by the user via
    the GUI or invtool. Inventory makes sure that these real range objects are
    always within the bounds of their parent network and that no two ranges
    overlap.

    What happens to the template ranges when a real range is defined inside an
    Inventory network?

    For example::

        10.8.0.0                                                     10.8.0.255
        |------------------------------------------------------....--|
         |-- template --|           |----- user defined range -----|
         10.8.0.1     10.8.0.10     10.8.0.50                      10.8.0.100


    In this case both the template range and the user defined range is
    returned.

    Another example::

        10.8.0.0                                                     10.8.0.255
        |------------------------------------------------------....--|
                            |----- template ------|
                            10.8.0.15            10.8.0.60
         |-- template --|           |----- user defined range ----|
         10.8.0.1     10.8.0.10     10.8.0.50                      10.8.0.100

    In this case the overlapping template range is filtered out.


    This function looks at the ranges in the db and removed template ranges
    that overlap with real ranges. This function also injects the real ranges
    in with the template ranges.

    The return format is the same as :func:`calc_ranges`.
    """
    real_ranges = network.range_set.all()
    if not real_ranges:
        return template_ranges

    name_fragment = calc_name_fragment(network)
    dhcp_scope = network.calc_dhcp_scope_name()
    filtered_ranges = []
    no_ovlp_templates = []

    for tr in template_ranges:
        ol = False
        for r in real_ranges:
            ol = overlap(
                (r.start_str, r.end_str), (tr['start'], tr['end']),
                ip_type=network.ip_type, cast_to_int=True
            )
            if ol:
                break

        if not ol:
            no_ovlp_templates.append(tr)

    for r in real_ranges:
        filtered_ranges.append({
            'name': r.name,
            'rtype': r.name,
            'start': r.start_str,
            'end': r.end_str,
            'dhcp_scope': dhcp_scope,
            'name_fragment': name_fragment,
            'pk': r.pk
        })

    filtered_ranges += no_ovlp_templates

    return sorted(
        filtered_ranges, key=lambda r: ip_to_int(r['start'], network.ip_type)
    )


def calc_name_fragment(network, base_name=''):
    """
    Suggest some names given a network
    """
    if network.site:
        base_name = network.site.full_name

    if network.vlan:
        base_name = '.'.join([network.vlan.name, base_name])

    return base_name
