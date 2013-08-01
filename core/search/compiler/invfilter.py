import operator
import re
import ipaddr

from itertools import izip

from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import ValidationError
from django.db.models import Q

from mozdns.address_record.models import AddressRecord
from mozdns.cname.models import CNAME
from mozdns.domain.models import Domain
from mozdns.mx.models import MX
from mozdns.nameserver.models import Nameserver
from mozdns.ptr.models import PTR
from mozdns.srv.models import SRV
from mozdns.soa.models import SOA
from mozdns.sshfp.models import SSHFP
from mozdns.txt.models import TXT
from mozdns.view.models import View

from core.registration.static.models import StaticReg
from core.site.models import Site
from core.network.models import Network
from core.network.utils import calc_networks_str
from core.utils import IPFilter, one_to_two
from core.vlan.models import Vlan
from core.utils import start_end_filter, resolve_ip_type
from core.search.utils import objects_to_Q

from systems.models import System, SystemRack


class BadDirective(Exception):
    pass


class BadType(Exception):
    pass


searchables = (
    ('A', AddressRecord),
    ('CNAME', CNAME),
    ('DOMAIN', Domain),
    ('MX', MX),
    ('NS', Nameserver),
    ('PTR', PTR),
    ('SOA', SOA),
    ('SRV', SRV),
    ('SSHFP', SSHFP),
    ('SREG', StaticReg),
    ('SYSTEM', System),
    ('RACK', SystemRack),
    ('TXT', TXT),
    ('NET', Network),
    ('SITE', Site),
    ('VLAN', Vlan),
)


class _Filter(object):
    """The Base class of different filters. Implement these methods
    """
    ntype = "FILTER"

    def __str__(self):
        return self.value

    def __repr__(self):
        return "<{1}>".format(self.__class__, self)

    def compile_Q(self):
        pass


def build_filter(filter_, fields, filter_type):
    # rtucker++
    final_filter = Q()
    for t in fields:
        final_filter = final_filter | Q(
            **{"{0}__{1}".format(t, filter_type): filter_})

    return final_filter


class TextFilter(_Filter):
    def __init__(self, rvalue):
        self.value = rvalue

    def compile_Q(self):
        # Value is the search term
        result = []
        for name, Klass in searchables:
            result.append(
                build_filter(self.value, Klass.search_fields, 'icontains'))
        return result


class REFilter(TextFilter):
    num_match = re.compile("\{(\d+)-(\d+)\}")

    def _expand_number_regex(self, value):
        """
        We want to turn something like /hp-node{31-40}.phx1 into
            '/hp-node(31|32|33|34|35|36|37|38|39|40).phx1'
        """
        matches = self.num_match.findall(value)
        for low, high in matches:
            padding = min(len(low), len(high))
            if int(low) >= int(high):
                continue
            new_value = ""
            for i in xrange(int(low), int(high) + 1):
                new_value += "{0}|".format(str(i).rjust(padding, '0'))
            new_value = '(' + new_value.strip('|') + ')'
            value = value.replace('{{{0}-{1}}}'.format(low, high), new_value)
        return value

    def compile_Q(self):
        result = []
        value = self._expand_number_regex(self.value)
        for name, Klass in searchables:
            result.append(build_filter(value, Klass.search_fields, 'regex'))
        return result


class DirectiveFilter(_Filter):
    def __init__(self, directive, dvalue):
        self.directive = directive
        self.dvalue = dvalue

    def compile_Q(self):
        if self.directive == 'view':
            return build_view_qsets(self.dvalue)
        elif self.directive == 'network':
            return build_network_qsets(self.dvalue)
        elif self.directive == 'vlan':
            return build_vlan_qsets(self.dvalue)
        elif self.directive == 'zone':
            return build_zone_qsets(self.dvalue)
        elif self.directive == 'range':
            return build_range_qsets(self.dvalue)
        elif self.directive == 'type':
            return build_rdtype_qsets(self.dvalue)
        elif self.directive == 'site':
            return build_site_qsets(self.dvalue)
        elif self.directive == 'ip':
            return build_ip_qsets(self.dvalue)
        else:
            raise BadDirective(
                "Unknown Directive '{0}'".format(self.directive)
            )


def build_rdtype_qsets(rdtype):
    """This function needs to filter out all records of a certain rdtype (like
    A or CNAME). Any filter produced here has to be able to be negated. We use
    the fact that every object has a pk > -1. When a qset is negated the query
    becomes pk <= -1.
    """
    rdtype = rdtype.upper()  # Let's get consistent
    select = Q(pk__gt=-1)
    no_select = Q(pk__lte=-1)
    result = []
    found_type = False
    for name, Klass in searchables:
        if name == rdtype:
            result.append(select)
            found_type = True
        else:
            result.append(no_select)
    if not found_type:
        raise BadType("Type '{0}' does not exist!".format(rdtype))
    return result


def build_view_qsets(view_name):
    """Filter based on DNS views."""
    view_name = view_name.lower()  # Let's get consistent
    try:
        view = View.objects.get(name=view_name)
    except ObjectDoesNotExist:
        raise BadDirective("'{0}' isn't a valid view.".format(view_name))
    view_filter = Q(views=view)  # This will slow queries down due to joins
    q_sets = []
    select = Q(pk__gt=-1)
    for name, Klass in searchables:
        if name == 'SOA':
            q_sets.append(select)  # SOA's are always public and private
        elif hasattr(Klass, 'views'):
            q_sets.append(view_filter)
        else:
            q_sets.append(None)
    return q_sets


def build_ipf_qsets(q):
    """Filter based on IP address views.
    :param q: A filter for a certain IP or IP range
    :type q: Q
    """
    q_sets = []
    for name, Klass in searchables:
        if name == 'A' or name == 'SREG' or name == 'PTR':
            q_sets.append(q)
        else:
            q_sets.append(None)
    return q_sets


def build_range_qsets(range_):
    try:
        start, end = range_.split(',')
    except ValueError:
        raise BadDirective("Specify a range using the format: start,end")
    start_ip_type, _ = resolve_ip_type(start)
    end_ip_type, _ = resolve_ip_type(end)
    if start_ip_type != end_ip_type or not start_ip_type or not end_ip_type:
        raise BadDirective("Couldn not resolve IP type of {0} and "
                           "{1}".format(start, end))
    try:
        istart, iend, ipf_q = start_end_filter(start, end, start_ip_type)
    except (ValidationError, ipaddr.AddressValueError), e:
        raise BadDirective(str(e))
    return build_ipf_qsets(ipf_q)


def build_ip_qsets(ip_str):
    """
    Possible objects returned:
        * A/PTR/SREG
        * Network
        * Vlan
        * Site
    """
    ip_type, Klass = resolve_ip_type(ip_str)

    NetworkCls = ipaddr.IPv4Network if ip_type == '4' else ipaddr.IPv6Network
    try:
        ip = NetworkCls(ip_str).network
        network_str = str(NetworkCls(ip_str))
    except ipaddr.AddressValueError:
        raise BadDirective("{0} isn't a valid "
                           "IP address.".format(ip_str))
    except ipaddr.NetmaskValueError, e:
        raise BadDirective(
            "The netmask '{0}' doesn't make any sense.".format(e)
        )

    try:
        network = Network.objects.get(network_str=network_str)
        network_q = objects_to_Q([network])
        site = network.site
        vlan = network.vlan
    except Network.DoesNotExist:
        parents, children = calc_networks_str(str(NetworkCls(ip_str)), ip_type)
        network_q = objects_to_Q(parents) | objects_to_Q(children)

        # Find the site. This will be the site of the smallest network that is
        # in parents or if there are no parents, the largest child.
        site = None
        vlan = None
        for parent in reversed(parents):
            if parent.site:
                site = parent.site
                vlan = parent.vlan
                break

        if not site:
            for child in children:
                if child.site:
                    site = child.site
                    vlan = child.vlan
                    break

    ip_upper, ip_lower = one_to_two(int(ip))

    ipf_qs = build_ipf_qsets(Q(ip_upper=ip_upper, ip_lower=ip_lower))
    q_sets = []

    for q, (name, Klass) in izip(ipf_qs, searchables):
        if name == 'NET':
            q_sets.append(network_q)
        elif name == 'SITE' and site:
            q_sets.append(Q(pk=site.pk))
        elif name == 'VLAN' and vlan:
            q_sets.append(Q(pk=vlan.pk))
        else:
            q_sets.append(q)

    return q_sets


def build_network_qsets(network_str):
    ip_type, Klass = resolve_ip_type(network_str)
    try:
        network = Klass(network_str)
        ipf = IPFilter(network.network, network.broadcast, ip_type)
    except (ipaddr.AddressValueError, ipaddr.NetmaskValueError):
        raise BadDirective(
            "{0} isn't a valid network.".format(network_str)
        )
    return build_ipf_qsets(ipf.Q)


def build_site_single_qset(site):
    site_q = build_ipf_qsets(site.compile_Q())
    q_sets = []
    for q, (name, Klass) in izip(site_q, searchables):
        if name in ('RACK', 'NET'):
            q_sets.append(Q(site=site))
        elif name == 'SITE':
            q_sets.append(Q(pk=site.pk) | Q(parent=site))
        else:
            q_sets.append(q)

    return q_sets


def build_site_qsets(site_name):
    # Look for a more specific results first
    sites = Site.objects.filter(full_name=site_name)
    if not sites:
        sites = Site.objects.filter(name=site_name)
    if not sites:
        raise BadDirective(
            "{0} isn't a valid site.".format(site_name)
        )

    def combine(q1, q2):
        q_sets = []
        for x, y in izip(q1, q2):
            if not (x and y):
                q_sets.append(None)
            else:
                q_sets.append(x | y)
        return q_sets

    site_qs = map(build_site_single_qset, sites)
    x = reduce(combine, site_qs)
    return x


def resolve_vlans(vlan_str):
    """
        case 0: vlan_str is <name>,<number>
        case 1: vlan_str is <number>,<name>
        case 2: vlan_str is <number>
        case 3: vlan_str is <name>
    """
    try:
        # Case 0
        vlan_name, vlan_number = vlan_str.split(',')
        if vlan_name.isdigit():
            vlan_name, vlan_number = vlan_number, vlan_name
        vlans = Vlan.objects.filter(number=vlan_number, name=vlan_name)
    except ValueError:
        # Case 1 and 2
        if vlan_str.isdigit():
            vlans = Vlan.objects.filter(number=vlan_str)
        else:
            vlans = Vlan.objects.filter(name=vlan_str)
    if not vlans.exists():
        raise BadDirective(
            "{0} doesn't resolve to a vlan Inventory knows "
            "about.".format(vlan_str)
        )
    return vlans


def make_vlan_q_set(vlan):
    ip_qs = build_ipf_qsets(vlan.compile_Q())
    q_sets = []
    for q, (name, Klass) in izip(ip_qs, searchables):
        if name in ('NET'):
            q_sets.append(vlan.compile_network_Q())
        elif name == 'VLAN':
            q_sets.append(Q(pk=vlan.pk))
        else:
            q_sets.append(q)
    return q_sets


def build_vlan_qsets(vlan_str):
    """
    To use this directive you should use the 'vlan=:' directive. Vlan's have a
    number and a name and some vlan's have the same number/name. If you specify
    a vlan name that maps back to two different vlans, both vlans and their
    corresponding objects will be displayed. To specify a vlan number -and-
    name, comma seperate (no spaces in between) the number and name. Some
    examples::

        vlan=:foo,23
        vlan=:23,foo
        vlan=:foo
        vlan=:23

    """
    vlans = resolve_vlans(vlan_str)
    vlan_qs = map(make_vlan_q_set, vlans)

    def OR(l1, l2):
        q_sets = []
        for i, j in izip(l1, l2):
            if i is None and j is None:
                q_sets.append(None)
            else:
                q_sets.append(i | j)
        return q_sets

    return reduce(OR, vlan_qs)


def build_zone_qsets(zone):
    """The point of this filter is to first find the root of a dns zone
    specified by zone and then build a query to return all records in this
    zone.
    """
    try:
        root_domain = Domain.objects.get(name=zone)
        # This might not actually be the root of a zone, but functionally we
        # don't really care.
    except ObjectDoesNotExist:
        raise BadDirective("'{0}' part of a valid zone.".format(zone))

    if not root_domain.soa:
        raise BadDirective("'{0}' part of a valid zone.".format(zone))

    def _get_zone_domains(domain):
        domains = [domain]
        for sub_domain in domain.domain_set.filter(soa=domain.soa):
            domains += _get_zone_domains(sub_domain)
        return domains

    zone_domains = _get_zone_domains(root_domain)

    domains = [Q(domain=domain) for domain in zone_domains]
    reverse_domains = [Q(reverse_domain=domain) for domain in zone_domains]

    zone_query = reduce(operator.or_, domains, Q())
    reverse_zone_query = reduce(operator.or_, reverse_domains, Q())

    result = []
    for name, Klass in searchables:
        if hasattr(Klass, 'domain'):
            result.append(zone_query)
        elif hasattr(Klass, 'reverse_domain'):
            result.append(reverse_zone_query)
        elif name == 'SOA':
            result.append(Q(pk=root_domain.soa.pk))
        else:
            result.append(None)
    return result
