import operator
import ipaddr
import pdb

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
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

from core.interface.static_intr.models import StaticInterface
from core.site.models import Site
from core.utils import two_to_four, IPFilter
from core.vlan.models import Vlan

from systems.models import System


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
        ('INTR', StaticInterface),
        ('SYSTEM', System),
        ('TXT', TXT),
)

def get_managers():
    managers = []
    for name, Klass in searchables:
        if name == 'System':
            managers.append(Klass.objectsselect_related('server_model',
                            'system_rack__location'))
        else:
            managers.append(Klass.objects)
    return managers

class _Filter(object):
    """The Base class of different filters. Implement these methods
    """
    ntype = "FILTER"
    def __str__(self):
        return self.value

    def __repr__(self):
        return "<{1}>".format(self.__class__, self)

    def compile_Q(self, ntype):
        pass


def build_filter(filter_, fields, filter_type):
    # rtucker++
    final_filter = Q()
    for t in fields:
        final_filter = final_filter | Q(**{"{0}__{1}".format(t,
            filter_type): filter_})

    return final_filter


class TextFilter(_Filter):
    def __init__(self, rvalue):
        self.value = rvalue
        self.Q = self.compile_Q(rvalue)

    def compile_Q(self, value):
        # Value is the search term
        result = []
        for name, Klass in searchables:
            result.append(build_filter(value, Klass.search_fields, 'icontains'))
        return result


class REFilter(TextFilter):
    def compile_Q(self, value):
        result = []
        for name, Klass in searchables:
            result.append(build_filter(value, Klass.search_fields, 'regex'))
        return result


class DirectiveFilter(_Filter):
    def __init__(self, rvalue, directive, dvalue):
        self.value = rvalue
        self.directive = directive
        self.dvalue = dvalue
        self.Q = self.compile_Q(directive, dvalue)

    def compile_Q(self, directive, dvalue):
        if directive == 'view':
            return build_view_qsets(dvalue)
        elif directive == 'network':
            return build_network_qsets(dvalue)
        elif directive == 'vlan':
            return build_vlan_qsets(dvalue)
        elif directive == 'zone':
            return build_zone_qsets(dvalue)
        elif directive == 'type':
            return build_rdtype_qsets(dvalue)
        elif directive == 'site':
            return build_site_qsets(dvalue)
        else:
            raise BadDirective("Unknown Directive '{0}'".format(directive))



##############################################################################
##########################  Directive Filters  ###############################
##############################################################################


class BadDirective(Exception):
    pass


def build_rdtype_qsets(rdtype):
    """This function needs to filter out all records of a certain rdtype (like
    A or CNAME). Any filter produced here has to be able to be negated. We use
    the fact that every object has a pk > -1. When a qset is negated the query
    becomes pk <= -1.
    """
    rdtype = rdtype.upper() # Let's get consistent
    select = Q(pk__gt=-1)
    no_select = Q(pk__lte=-1)
    result = []
    for name, Klass in searchables:
        if name == rdtype:
            result.append(select)
        else:
            result.append(no_select)
    return result

def build_view_qsets(view_name):
    """Filter based on DNS views."""
    view_name = view_name.lower()  # Let's get consistent
    try:
        view = View.objects.get(name=view_name)
    except ObjectDoesNotExist:
        raise BadDirective("'{0}' isn't a valid view.".format(view_name))
    view_filter = Q(views=view) # This will slow queries down due to joins
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
        if name == 'A' or name == 'INTR' or name == 'PTR':
            q_sets.append(q)
        else:
            q_sets.append(None)
    return q_sets

def build_network_qsets(network_str):
    # Todo move these directive processors into functions.
    if network_str.find(':') > -1:
        Klass = ipaddr.IPv6Network
        ip_type = '6'
    if network_str.find('.') > -1:
        Klass = ipaddr.IPv4Network
        ip_type = '4'
    try:
        network = Klass(network_str)
        ip_info = two_to_four(int(network.network),
                              int(network.broadcast))
        ipf = IPFilter(None, ip_type, *ip_info)
    except (ipaddr.AddressValueError, ipaddr.NetmaskValueError), e:
        raise BadDirective("{0} isn't a valid "
                "network.".format(network_str))
    return build_ipf_qsets(ipf.compile_Q())


def build_site_qsets(site_name):
    try:
        site = Site.objects.get(name=site_name)
    except ObjectDoesNotExist, e:
        raise BadDirective("{0} isn't a valid "
                "site.".format(site_name))
    return build_ipf_qsets(site.compile_Q('4'))


def build_vlan_qsets(vlan_name):
    try:
        if vlan_name.isdigit():
            vlan = Vlan.objects.get(number=vlan_name)
        else:
            vlan = Vlan.objects.get(name=vlan_name)
    except ObjectDoesNotExist, e:
        raise BadDirective("{0} isn't a valid "
                "vlan identifier.".format(vlan_name))
    except MultipleObjectsReturned, e:
        raise BadDirective("{0} doesn't uniquely identify"
                "a vlan.".format(vlan_name))
    return build_ipf_qsets(vlan.compile_Q('4'))


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

    domains = _get_zone_domains(root_domain)

    if root_domain.is_reverse:
        domains = [Q(reverse_domain=domain) for domain in domains]
    else:
        domains = [Q(domain=domain) for domain in domains]

    zone_query = reduce(operator.or_, domains, Q())

    result = []
    for name, Klass in searchables:
        if hasattr(Klass, 'domain') and not root_domain.is_reverse:
            result.append(zone_query)
        elif hasattr(Klass, 'reverse_domain') and root_domain.is_reverse:
            result.append(zone_query)
        elif name == 'SOA':
            result.append(Q(pk=root_domain.soa.pk))
        else:
            result.append(None)
    return result
