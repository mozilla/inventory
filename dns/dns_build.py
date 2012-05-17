from truth.models import Truth
from systems.models import System
from dns.build_nics import *

import ipaddr

import re
import copy
import pprint

pp = pprint.PrettyPrinter(indent=2)


def do_dns_build():
    forward, reverse = build_sites([
                ('dmz.scl3', '10.22.1.0/24'),
                ('private.scl3', '10.22.75.0/24')
            ])
    print "=" * 10 + "Forward sites" + "=" * 10
    pp.pprint(forward)
    print "=" * 10 + "Reverse sites" + "=" * 10
    pp.pprint(reverse)


def generate_hostname(hostname, site_name, nic_meta_data):
    """
    Determine the correct fqdn from the nic's hostname key, site the name is
    going into, and any other additional options in nic_meta_data.

    :param hostname: The hostname on the nic.
    :type hostname: str
    :param site_name: The site_name that this nic's ip is in.
    :type site_name: str
    :param nic_meta_data: Other options that pertain to the nic.
    :type nic_meta_data: dict.
    :return build_hostname: The hostname to use in the A/PTR record.
    :type build_hostname: str
    """
    # Hey look Values are stored as strings.
    if nic_meta_data.get('dns_build_options', {}).get('dns_auto_hostname',
            'True') == 'False':
        return hostname
    if len(hostname.split('.')) == 1:
        return "{0}.{1}.mozilla.com".format(hostname, site_name)
    else:
        return "{0}.mozilla.com".format(hostname)


def build_sites(sites):
    """
    For each site in sites partition data into logical site groups. Later these
    groups will be used to print BIND Zone files.

    Sites have the form::

        ('<vlan-name>.<site-name>', <'network-mask'>)

    For example::

        ('dmz.scl3', '10.22.1.0/24')

    :param sites: The sites that data should be aggrigated for.
    :type sites: tuple

    This function returns data in the form of two dicts: one for forward sites
    and one for reverse zones.

    ==========Forward sites==========
    { 'dmz.scl3': ( IPv4Network('10.22.1.0/24'),
                   [('kvm1.private.releng.scl3.mozilla.com', u'10.22.1.229')]),
                    ...
                    ...

      'private.scl3': ( IPv4Network('10.22.75.0/24'),
                        [ ( 'rhel5dev32.private.scl3.mozilla.com',
                            u'10.22.75.65'),
                          ( 'im-pkgdev03.private.scl3.mozilla.com',
                            u'10.22.75.66'),
                          ('puppet1.private.scl3.mozilla.com', u'10.22.75.36'),
                          ('puppet1.private.scl3.mozilla.com', u'10.22.75.36'),
                          ('ns1.private.scl3.mozilla.com', u'10.22.75.40'),
                          ('ns1.private.scl3.mozilla.com', u'10.22.75.40'),
                          ('ns2.private.scl3.mozilla.com', u'10.22.75.41'),
                    ...
                    ...
                    ...

    ==========Reverse sites==========
    { u'10.22.1': [(u'10.22.1.229', 'kvm1.private.releng.scl3.mozilla.com')],
                    ...
                    ...

      u'10.22.75': [ (u'10.22.75.65', 'rhel5dev32.private.scl3.mozilla.com'),
                     (u'10.22.75.66', 'im-pkgdev03.private.scl3.mozilla.com'),
                     (u'10.22.75.36', 'puppet1.private.scl3.mozilla.com'),
                    ...
                    ...

    """
    # Aggregated data goes in these dicts.
    agg_sites = {}
    agg_reverse = {}
    for site in sites:
        # Pre-calculate the regular expressions so we can do this in one pass.
        name, network = site
        # Add address family logic here if need be.
        try:
            agg_sites[name] = (ipaddr.IPv4Network(network), [])
        except ipaddr.AddressValueError, e:
            # Eventually send an email or do something more serious about an
            # error here.
            print str(e)

    def sanity_check(hostnames):
        if len(hostnames) == 1:
            return True
        if hostnames[0] != hostnames[1]:
            return True
        else:
            return sanity_check(hostnames[1:])

    for nic in get_dns_data():
        # BAH! This isn't a FQDN (hostname), it's more likely a single or
        # multiple label(s).
        ips, macs, hostname, nic_meta_data = nic
        # Yeah! Values are stored as strings. Let's remember not to do that for
        # the next version of this.
        if nic_meta_data.get('dns_build_options', {}).get('dns_auto_build',
                'True') == 'False':
            # This nick is flagged not to be part of the dns builds.
            continue

        # Sanity check. All the hostnames should be the same.
        if not sanity_check(hostname):
            print "ERROR: Sanity check failed on nic {0}".format(nic)
            continue
        hostname = hostname[0]

        for site_name, data in agg_sites.items():
            network, entries = data
            for ip in ips:
                if ipaddr.IPv4Network(ip).overlaps(network):
                    fqdn = generate_hostname(hostname, site_name,
                            nic_meta_data)
                    entries.append((fqdn, ip))
                    rev_file_name = '.'.join(ip.split('.')[:3])
                    reverse_data = agg_reverse.setdefault(rev_file_name, [])
                    reverse_data.append((ip, fqdn))
                # TODO Should we add all hosts to reverse zones? Even if it
                # doesn't belong to a site?  Or should we only add to the
                # reverse when there is a corresponding record A in forward?
                # For now only add if we find a forward match. I'm pretty sure
                # there is an RFC that says A records should always have a PTR.
                # Is that the same for PTR's?

    return (agg_sites, agg_reverse)
