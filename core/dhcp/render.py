from core.registration.static.models import StaticReg

import hashlib

# This doesn't work for IPv6... yet


def render_statements(statements, **kwargs):
    return _render_kv(statements, **kwargs)


def render_options(options, **kwargs):
    return _render_kv(options, type_='option', **kwargs)


def _render_kv(kvs, type_='', tabs=1):
    build_str = ''
    if kvs:
        if type_:
            prefix = type_ + ' '  # The space is important!
        else:
            prefix = type_
        for kv in kvs:
            build_str += "{0}{1}{2:20} {3};\n".format(
                '\t' * tabs, prefix, kv.key.replace('_', '-'), kv.value
            )
        build_str += "\n"
    return build_str


def render_host(fqdn, ip_str, mac, i_n, options, statements, tabs=2):
    m = hashlib.md5()
    m.update(fqdn + ip_str + mac + i_n)
    unique_identifier = m.hexdigest()
    # XXX Better way to generate unique_identifier ?

    build_str = ''
    build_str += "{0}host {1}-{2}-{3} {{\n".format(
        '\t' * (tabs - 1), fqdn, i_n, unique_identifier
    )
    build_str += "{0}hardware ethernet {1};\n".format('\t' * tabs, mac)
    build_str += "{0}fixed-address {1};\n".format('\t' * tabs, ip_str)
    build_str += render_statements(statements, tabs=tabs)
    if not options.filter(key='host_name').exists():
        build_str += "{0}option host-name \"{1}\";\n".format('\t' * tabs, fqdn)
    build_str += render_options(options, tabs=tabs)
    build_str += "{0}}}\n\n".format('\t' * (tabs - 1))
    return build_str


def render_sreg(sreg, hw, tabs=2):
    build_str = ''
    options = hw.keyvalue_set.filter(is_option=True)
    statements = hw.keyvalue_set.filter(is_statement=True)
    build_str += render_host(
        sreg.fqdn, sreg.ip_str, hw.mac, hw.name, options,
        statements, tabs=tabs
    )
    return build_str


def render_sregs(sregs):
    build_str = ''
    groups = {}
    for sreg in sregs:
        if sreg.decommissioned:
            continue
        hws = sreg.hwadapter_set.filter(enable_dhcp=True).order_by('mac')
        for hw in hws:
            if hw.group:
                # If this host belongs to a group we will render it, and any
                # other adapters in the group, at a latter time.
                groups.setdefault(
                    hw.group.name, (hw.group, [])
                )[1].append((sreg, hw))
            else:
                build_str += render_sreg(sreg, hw)
    if groups:
        for group_name, (group, bundle) in groups.iteritems():
            build_str += "\tgroup {{  # group {0}\n\n".format(group_name)
            group_options = group.keyvalue_set.filter(is_option=True)
            group_statements = group.keyvalue_set.filter(is_statement=True)
            build_str += render_statements(group_statements, tabs=2)
            build_str += render_options(group_options, tabs=2)
            for sreg, hw in bundle:
                build_str += render_sreg(sreg, hw, tabs=3)
            build_str += "\t}\n\n"

    return build_str


def render_subnet(network):
    """
    The core function of building DHCP files.

    :param network: The network that will be searched for
        :ref:`StaticReg` instances.
    :type network: :class:`StaticReg`
    """
    network_options = network.keyvalue_set.filter(is_option=True)
    network_statements = network.keyvalue_set.filter(is_statement=True)
    network_raw_include = network.dhcpd_raw_include
    # All interface objects that are within this network and have enable_dhcp.
    # TODO, make this work with IPv6
    if network.ip_type == '6':
        raise NotImplemented()
    network.update_network()
    ip_lower_start = int(network.network.network)
    ip_lower_end = int(network.network.broadcast) - 1
    sregs = StaticReg.objects.filter(
        ip_upper=0,
        ip_lower__gte=ip_lower_start,
        ip_lower__lte=ip_lower_end,
        ip_type='4'
    ).select_related()
    ranges = network.range_set.all()

    # Let's assume all options need a ';' appended.
    build_str = "# Generated DHCP \n\n"
    build_str += "subnet {0} netmask {1} {{\n\n".format(
        network, network.network.netmask)
    build_str += "\t# Network Statements\n"
    build_str += render_statements(network_statements)
    build_str += "\t# Network Options\n"
    build_str += render_options(network_options)

    if network_raw_include:
        for line in network_raw_include.split('\n'):
            build_str += "\t{0}\n".format(line)
    build_str += "\n"

    for mrange in ranges:
        build_str += render_pool(mrange)

    build_str += render_sregs(sregs)

    build_str += "}"
    return build_str


def render_pool(mrange):
    pool_options = mrange.keyvalue_set.filter(is_option=True)
    pool_statements = mrange.keyvalue_set.filter(is_statement=True)

    build_str = "\tpool {\n"
    build_str += "\t\t# Pool Statements\n"
    build_str += render_statements(pool_statements, tabs=2)
    build_str += "\t\t# Pool Options\n"
    build_str += render_options(pool_options, tabs=2)
    build_str += "\n"

    if mrange.dhcpd_raw_include:
        build_str += "\t\t{0}\n".format(mrange.dhcpd_raw_include)

    build_str += "\t\trange {0} {1};\n".format(
        mrange.start_str, mrange.end_str
    )

    build_str += "\t}\n\n"
    return build_str
