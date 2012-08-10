from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.exceptions import MultipleObjectsReturned
from django.forms.util import ErrorDict, ErrorList

from core.site.models import Site
from core.vlan.models import Vlan
from core.site.models import Site
from core.interface.static_intr.models import StaticInterface

from mozdns.domain.models import Domain
import pdb
import re

is_mozilla_tld = re.compile(".*mozilla\.(org|net|ru|co|it|me|de|hu|pt|"
        "at|uk|rs|la|tv)$")

def create_ipv4_intr_from_domain(label, domain_name, system, mac):
    """A wrapper for `create_ipv4_interface`."""
    if is_mozilla_tld.match(domain_name):
        d = domain_name.split('.')[:-2]
        domain_suffix = '.'.join(d[-2:])
    else:
        # It's probably a mozilla.com TLD
       d_str = domain_name.replace("mozilla.com","")
       d = d_str.split('.')
       domain_suffix = "mozilla.com"

    vlan_str = d[0]
    datacenter = ".".join(d[1:])

    return create_ipv4_interface(label, vlan_str, datacenter, system, mac,
                                domain_suffix)


def create_ipv4_interface(label, vlan_str, site_str, system,
                            mac, domain_suffix):
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

    try:
        network = vlan.network_set.get(site=site)
    except MultipleObjectsReturned, e:
        errors['network'] = ErrorList(["There were too many networks "
                "associated with vlan {0} in {1}. Manually specify which "
                "network to use.".format(vlan, site)])
        return None, errors
    except ObjectDoesNotExist, e:
        errors['network'] = "No network for vlan {0} in {1}.".format(vlan, site)
        return None, errors

    if not network.range_set.all().exists():
        errors['range'] = ErrorList(["No range for network {0} in vlan {1} in "
            "site {0}. Create it via the web UI too many networks associated "
            "with vlan {0} in {1}".format(network, vlan, site)])
        return None, errors

    ip = None
    for range_ in network.range_set.all():
        ip = range_.get_next_ip()

    if not ip:
        errors['ip'] = ErrorList(["Could not find free ip in range."])
        return None, errors

    try:
        intr = StaticInterface(label=label, domain=domain, ip_str=str(ip),
            ip_type='4', system=system, mac=mac)
        intr.clean()
    except ValidationError, e:
        errors['interface'] = ErrorList(e.messages)
        return None, errors

    return intr, None
