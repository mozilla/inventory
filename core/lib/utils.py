from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.models import Q
from django.core.exceptions import MultipleObjectsReturned
from django.forms.util import ErrorDict, ErrorList

from core.site.models import Site
from core.vlan.models import Vlan
from core.network.models import Network
from core.site.models import Site
from core.range.models import find_free_ip
from core.interface.static_intr.models import StaticInterface

from mozdns.utils import ensure_domain
from mozdns.ip.utils import i64_to_i128, i128_to_i64
from mozdns.domain.models import Domain
from mozdns.address_record.models import AddressRecord
from mozdns.ptr.models import PTR


import pdb
import re
import ipaddr

is_mozilla_tld = re.compile(".*mozilla\.(org|net|ru|co|it|me|de|hu|pt|"
        "at|uk|rs|la|tv)$")

def create_ipv4_intr_from_domain(
        label, domain_name, system, mac,
        specific_site=False):
    """A wrapper for `create_ipv4_interface`."""

def create_ipv4_intr_from_domain(label, domain_name, system, mac,
        network_str=None):
    """A wrapper for :func:`create_ipv4_interface`."""
    if is_mozilla_tld.match(domain_name):
        d = domain_name.split('.')[:-2]
        domain_suffix = '.'.join(d[-2:])
    else:
        # It's probably a mozilla.com TLD
       d_str = domain_name.replace(".mozilla.com","")
       d = d_str.split('.')
       domain_suffix = "mozilla.com"

    vlan_str = d[0]
    datacenter = ".".join(d[1:])

    return create_ipv4_interface(label, vlan_str, datacenter, system, mac,
                                domain_suffix, network_str)


def create_ipv4_interface(label, vlan_str, site_str, system,
                            mac, domain_suffix, network_str=None):
    """This is an api for creating an interface.

    :param label: The label of the interface.
    :type lavel: str
    :param vlan_str: The name of the vlan the interface should be put into.
    :type vlan_str: str
    :param site_str: The Datacenter (and possibly the Buisness Unit) the vlan is in.
    :type site_str: str
    :param system: The system the interface belongs to.
    :type system: :class:`System`
    :param mac: The mac address of the new interface.
    :type mac: str
    :param domain_suffix: The suffix of the domain. This is usually
        'mozilla.com'.
    :type domain_suffix: str
    :param network_str: This is an optional paramter. If you get a
        :class:`MultipleObjectsReturned` error when trying to find a network,
        you can specify which network to use by passing the network's name
        using this kwarg. E.g. ``network="10.22.9.0/24"``
    :type network_str: str

    This function returns two values. The first value is the
    :class:`StaticInterface` instance. If the interface was succesfully created
    the second return value is meaningless. If there were errors while creating
    the interface the first value is None and the second return value is an
    ErrorDict containing errors that should be displayed to the user. Always
    check the first return value for being a NoneType.

    Using this function requires that certain objects exist in the database.
    *Understanding these objects before using this function is a good thing*.
    ::

                    <label> (.<BU>) .<DC> . <domain_suffix>

    1. This function starts by looking for a site in the site table that has a
        site path (i.e. `<BU>.<DC>` like 'relenge.scl3' or just 'scl3') equal to the
        'site_str' paramter.

        If you get errors from this step (i.e. There is a 'site' key in the
        errors dictionary), create the site you are trying to use in the Web UI.


    2.  The function then looks in the site found in Step 1 for a :class:`Vlan`
        instance with a name equal to the 'vlan_str' parameter.

        If you get errors from this step (i.e. There is a 'vlan' key in the
        errors dictionary), create the vlan you are trying to use in the Web
        UI.


    3.  Using the :class:`Site` and :class:`Vlan` instance found in Step 1 & 2 and
        the `domain_suffix` paramter, the function constructs the following
        string.::

            <vlan>.<site>.<domain_suffix>

        As an example, imaging we were using::

            site = relenge.scl3
            vlan = db
            domain_suffix = mozilla.com

        The constructed string would be::

            db.relenge.scl3.mozilla.com

        The function will now use this constructed string as the domain name for
        creating the interface's A/PTR records. For this reason *a domain with the
        constructed name _must_ be in the database*.

        If you get errors from this step (i.e. There is a 'domain' key in the errors
        dictionary), create the domain you are trying to use in the Web UI.


    4.  The function then looks at the networks associated with that vlan found in
        Step 2 and chooses the networks that are associated to the site found in
        Step 1.

        If you get errors from this step (i.e. There is a 'network' key in the errors
        dictionary), create the network you are trying to use in the Web UI and
        associate it with the vlan *and* site you are trying to use.


    5.  The function then looks for ranges within the networks found in Step 4. If
        the function finds more than one range it does not make a choice for you
        and returns an error. If the function finds only one range it looks for a
        free IP in that range while returning an error if no free IP is found.

    6.  Using the 'label', 'system', 'mac', and IP address found in Step 4, a new
        StaticInterface is created. If there are errors while creating the
        Interface those errors are returned. If there are no errors while creating
        the Interface the Interface is returned.
    """
    errors = ErrorDict()
    if not label:
        errors['label'] = ErrorList(["Please supply a label."])
        return None, errors

    if not system:
        errors['system'] = ErrorList("Please supply a system.".format(site_str))
        return None, errors

    site = None
    for s in Site.objects.all():
        # get_site_path returns the path backwards, work around this.
        # TODO fix this.
        if '.'.join(list(reversed(s.get_site_path().split('.')))) == site_str:
            site = s
            break
    if not site:
        errors['site'] = ErrorList(["Site {0} does not exist".format(site_str)])
        return None, errors

    try:
        vlan = Vlan.objects.get(name=vlan_str)
    except ObjectDoesNotExist, e:
        errors['vlan'] = ErrorList(["Vlan {0} does not exist.".format(
            vlan_str)])
        return None, errors

    tmp_site_str = '.'.join(list(reversed(s.get_site_path().split('.'))))
    domain_name = vlan.name + "." + tmp_site_str + "." + domain_suffix
    try:
        domain = Domain.objects.get(name=domain_name)
    except ObjectDoesNotExist, e:
        errors['domain'] = ErrorList(["Could not find domain "
            "{0}".format(domain_name)])
        return None, errors

    if not network_str:
        try:
            network = vlan.network_set.get(site=site)
        except MultipleObjectsReturned, e:
            networks = vlan.network_set.filter(site=site)
            errors['network'] = ErrorList(["There were too many networks "
                    "associated with vlan {0} in {1}. Manually specify which "
                    "network to use. Your choces are {2}".format(vlan, site,
                    ", ".join([n.network_str for n in networks]))])
            return None, errors
        except ObjectDoesNotExist, e:
            errors['network'] = "No network for vlan {0} in {1}.".format(vlan, site)
            return None, errors
    else:
        try:
            # Guess which type of network it is.
            try:
                if network_str.find(':') > -1:
                    ip_type = '6'
                    tmp_network = ipaddr.IPv6Network(network_str)
                    ip_upper, ip_lower = ipv6_to_longs(network_str)
                else:
                    ip_type = '4'
                    tmp_network = ipaddr.IPv4Network(network_str)
                    ip_upper, ip_lower = 0, int(tmp_network)
            except ipaddr.AddressValueError, e:
                errors['network'] = ErrorList(["The network {0} is not a "
                    "valid IPv{1} network.".format(network_str, ip_type)])
                return None, errors
            # Now try to find a network that matches the query. Error out if we
            # can't find one and recommend the user create it.
            network = Network.objects.get(ip_type=ip_type, ip_upper=ip_upper,
                    ip_lower=ip_lower, prefixlen=tmp_network.prefixlen)
        except ObjectDoesNotExist, e:
                errors['network'] = ErrorList(["The network {0} was not "
                    "found. Consider creating it in the web UI.".format(
                    network_str)])
                return None, errors


    if not network.range_set.all().exists():
        errors['range'] = ErrorList(["No range for network {0} in vlan {1} in "
            "site {0}. Create it via the web UI too many networks associated "
            "with vlan {0} in {1}".format(network, vlan, site)])
        return None, errors

    if network.range_set.all().count() > 1:
        errors['ip'] = ErrorList(["Too many ranges. In the face of ambiguity, "
            "*this script* has refused the temptation to guess which range "
            "you want to put the interface in."])
        return None, errors

    range_ = network.range_set.all()[0]
    return _create_ipv4_intr_from_range(label, domain.name, system, mac,
            range_.start_lower, range_.end_lower)


def create_ipv4_intr_from_range(label, domain_name, system, mac,
        range_start_str, range_end_str):
    """This function creates an interface using the first free ip in the
    specified range. This function will also ensure that a :class:`Domain` with
    the name=``domain_name`` exists in the database. If a new domain is created
    it will enheirit it's master's SOA. If the name ``<label>.<domain_name>``
    is already a domain, the new interface's label will be set to the empty
    string.

    :param label: The desired label of the interface.
    :type lable: str
    :param domain_name: The name of the domain to create the interface in.
    :type domain_name: str
    :param system: The system object that the interface should be associated to
    :type system: :class:`System`
    :param mac: The mac address of the interface
    :type mac: str
    :param range_start_str: The IP where this function should start looking for
        a free ip (inclusive).
    :type range_start_str: str
    :param range_end_str: The last IP where this function should look for
        a free ip (inclusive).
    :type range_end_str: str
    """
    errors = ErrorDict()
    try:
        start = ipaddr.IPv4Address(range_start_str)
    except ipaddr.ValidationError, e:
        errors['ip'] = ErrorList(["Invalid IPv4 ip {0}".format(range_start_str)])
        return None, errors
    try:
        end = ipaddr.IPv4Address(range_end_str)
    except ipaddr.ValidationError, e:
        errors['ip'] = ErrorList(["Invalid IPv4 ip {0}".format(range_end_str)])
        return None, errors
    return _create_ipv4_intr_from_range(label, domain_name, system, mac,
            int(start), int(end))

def _create_ipv4_intr_from_range(label, domain_name, system, mac, range_start,
                                range_end):
    if range_start >= range_end -1:
        errors['ip'] = ErrorList(["The start ip must be less than end ip."])
        return None, errors

    ip = find_free_ip(range_start, range_end, ip_type='4')
    errors = ErrorDict()
    if not ip:
        errors['ip'] = ErrorList(["Could not find free ip in range {0} - "
                        "{1}".format(range_start, range_end)])
        return None, errors

    domain = ensure_domain(domain_name, inherit_soa=True)
    try:
        intr = StaticInterface(label=label, domain=domain, ip_str=str(ip),
                ip_type='4', system=system, mac=mac)
        intr.clean()
    except ValidationError, e:
        errors['interface'] = ErrorList(e.messages)
    return intr, None

def calc_free_ips_str(range_start_str, range_end_str, ip_type='4'):
    """This function counts the number of unused ip addresses in a range. An IP
    is considered 'used' if an A, PTR, or StaticInterface uses the IP.

    :param range_start_str: The IP where this function should start looking for
        a free ip (inclusive).
    :type range_start: str
    :param range_end_str: The last IP where this function should look for
        a free ip (inclusive).
    :type range_end: str
    """
    try:
        start = ipaddr.IPv4Address(range_start_str)
    except ipaddr.ValidationError, e:
        return None
    try:
        end = ipaddr.IPv4Address(range_end_str)
    except ipaddr.ValidationError, e:
        return None
    return calc_free_ips_int(int(start), int(end))


def calc_free_ips_int(range_start, range_end):
    """This function is like calc_free_ips_str except it's arguements are
    integers.
    """
    range_start_upper, range_start_lower = i128_to_i64(range_start)
    range_end_upper, range_end_lower = i128_to_i64(range_end)

    if range_start_upper == range_end_upper:
        ip_query = Q(ip_upper=range_start_upper, ip_lower__gte=range_start,
                ip_lower__lte=range_end_lower)
    else:
        ip_query = Q(ip_upper__gte=range_start_upper,
                ip_upper__lte=range_end_upper)

    records = AddressRecord.objects.filter(ip_query)
    ips = [record.ip_str for record in records]

    ptrs = PTR.objects.filter(ip_query)
    ips += [ptr.ip_str for ptr in ptrs]

    intrs = StaticInterface.objects.filter(ip_query)
    ips += [intr.ip_str for intr in intrs]

    return range_end - range_start - len(set(ips))
