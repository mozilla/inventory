from django.db.models import Q
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist

from mozdns.soa.models import SOA
from mozdns.validation import find_root_domain
from mozdns.mozbind.generators.bind_soa_generator import render_soa, render_soa_only
from mozdns.address_record.models import AddressRecord
from mozdns.cname.models import CNAME
from mozdns.domain.models import Domain
from mozdns.mx.models import MX
from mozdns.nameserver.models import Nameserver
from mozdns.ptr.models import PTR
from mozdns.soa.models import SOA
from mozdns.srv.models import SRV
from mozdns.txt.models import TXT
from mozdns.sshfp.models import SSHFP
from mozdns.view.models import View
from core.interface.static_intr.models import StaticInterface


import pdb
import os
import time

from settings import BUILD_PATH
from gettext import gettext as _
DEFAULT_TTL = 999

# DEBUG OPTIONS
DEBUG = True
DEBUG_BUILD_STRING = ''  # A string to store build output in.
CHROOT_ZONE_PATH = "/etc/invzones/"


def render_rdtype(rdtype_set, **kwargs):
    BUILD_STR = ""
    for obj in rdtype_set:
        BUILD_STR += _(obj.bind_render_record(**kwargs) + "\n")
    return BUILD_STR

def _render_reverse_zone(default_ttl, nameserver_set, interface_set, ptr_set):
    BUILD_STR = ''
    BUILD_STR += render_rdtype(nameserver_set)
    BUILD_STR += render_rdtype(ptr_set)
    BUILD_STR += render_rdtype(interface_set, reverse=True, rdtype='PTR')
    return BUILD_STR

def _render_forward_zone(default_ttl, nameserver_set, mx_set, addressrecord_set,
                interface_set, cname_set, srv_set, txt_set, sshfp_set):
    BUILD_STR = ""
    BUILD_STR += render_rdtype(nameserver_set)
    BUILD_STR += render_rdtype(mx_set)
    BUILD_STR += render_rdtype(txt_set)
    BUILD_STR += render_rdtype(sshfp_set)
    BUILD_STR += render_rdtype(srv_set)
    BUILD_STR += render_rdtype(cname_set)
    BUILD_STR += render_rdtype(interface_set, rdtype='A')
    BUILD_STR += render_rdtype(addressrecord_set)
    return BUILD_STR

def choose_zone_path(soa, root_domain):
    """This function decides where a zone's zone files go. If there is a key in
    the zone's KeyValue store called 'zone_path', that path is used. The path
    contained in 'zone_path' must exist on the file system.

    If no zone_path key is found. The following path is used:

    If the root_domain is a forward domain:

        * Replace all '.' characters with '/' characters.

    If the root_domain is a reverse domain:

        If it's ipv4

            'reverse/in-addr.arpa/'
            'reverse/in-addr.ipv6/'

    The build scripts will create this path on the filesystem if it does not
    exist.

    .. note::

        In all cases the zone_path is prepended with the ``BUILD_PATH`` varable
        found in ``settings/local.py``

    """
    soa.update_attrs()
    zone_path = None
    if root_domain.is_reverse:
        if root_domain.name.endswith('ipv6'):
            zone_path = "reverse/in-addr.arpa/"
        elif root_domain.name.endswith('arpa'):
            zone_path = "reverse/in-addr.arpa/"
        else:
            raise Exception("WTF type of reverse domain is this "
                    "{0}?!?".format(root_domain))
    else:
        try:
            zone_path = soa.attrs.dir_path
        except AttributeError, e:
            tmp_path = '/'.join(reversed(root_domain.name.split('.')))
            zone_path = tmp_path + '/'

    return zone_path


def render_forward_zone(view, mega_filter):
    data = _render_forward_zone(
            default_ttl=DEFAULT_TTL,

            nameserver_set=Nameserver.objects.filter(mega_filter
                ).filter(views__name=view.name).order_by('server'),

            mx_set=MX.objects.filter(mega_filter).filter(views__name=view.name
                ).order_by('server'),

            addressrecord_set=AddressRecord.objects.filter(mega_filter).filter(
                views__name=view.name).order_by('ip_type', 'label', 'ip_upper',
                    'ip_lower'),

            interface_set=StaticInterface.objects.filter(mega_filter,
                dns_enabled=True).filter(views__name=view.name).order_by(
                    'ip_type', 'label', 'ip_upper', 'ip_lower'),

            cname_set=CNAME.objects.filter(mega_filter).filter(
                views__name=view.name).order_by('label'),

            srv_set=SRV.objects.filter(mega_filter).filter(views__name=view.name
                ).order_by('label'),

            txt_set=TXT.objects.filter(mega_filter).filter(views__name=view.name
                ).order_by('label'),

            sshfp_set=SSHFP.objects.filter(mega_filter).filter(views__name=view.name
                ).order_by('label'),
        )
    return data


def render_reverse_zone(view, domain_mega_filter, rdomain_mega_filter):
    data = _render_reverse_zone(
            default_ttl=DEFAULT_TTL,

            nameserver_set=Nameserver.objects.filter(domain_mega_filter
                ).filter(views__name=view.name).order_by('server'),

            interface_set=StaticInterface.objects.filter(rdomain_mega_filter,
                dns_enabled=True).filter(views__name=view.name).order_by(
                    'ip_type', 'label', 'ip_upper', 'ip_lower'),

            ptr_set=PTR.objects.filter(rdomain_mega_filter).filter(views__name=view.name
                ).order_by('ip_upper').order_by('ip_lower'),

        )
    return data


def render_zone_stmt(zone_name, ns_type, file_path):
    zone_stmt = "\tzone \"{0}\" IN {{\n".format(zone_name)
    zone_stmt += "\t\ttype {0};\n".format(ns_type)
    zone_stmt += "\t\tfile \"{0}\";\n".format(file_path)
    zone_stmt += "\t};\n"
    return zone_stmt


def build_moz_zone(soa, domain_type, NOWRITE=True, request=None):
    user = request.META.get("USER", None)
    time_start = time.time()
    if domain_type == "forward":
        gen_moz_forward_zone(soa, NOWRITE=NOWRITE)
    elif domain_type == "reverse":
        gen_moz_reverse_zone(soa, NOWRITE=NOWRITE)
    else:
        return None
    time_end = time.time()
    time_total = time_end - time_start
    stats = {
            'soa_id': soa.pk,
            'time_start': time_start,
            'time_end': time_end,
            'time_total': time_total,
            'user': user
            }
    return stats


def build_zone(soa, RO=False):
    """Given an SOA, this function will generate the BIND data files and config
    statements (both for master and slave nameservers). This function also
    updates an SOA's serial. All files built by this function are writen to the
    stage directory. This function is responsible for calling
    ``named-checkconf`` and ``named-checkzone`` on the zone and config files it
    generates. If these checks fail this function will raise an exception.

    :param soa: The soa of the zone that should be built.
    :type soa: SOA
    :param RO: If the build should be readonly (no writes to the file system
               will be preformed)

    :returns DEBUG_BUILD_STRING: For debugging
    :type DEBUG_BUILD_STRING: str
    """
    soa.serial += 1
    # We are updating the local version of the soa. If this function succeeds
    # we will then save the SOA to the db.
    if not os.access(BUILD_PATH + zone_path, os.R_OK):
        os.makedirs(BUILD_PATH + zone_path)
    if private_data:
        DEBUG_STRING += ";{0} {1} View Data {0}\n".format("=" * 30, "Private")
        DEBUG_STRING += soa_data
        DEBUG_STRING += private_data

        master_private_zones = render_zone_stmt(root_domain.name, "master",
                CHROOT_ZONE_PATH + private_file_path)

        slave_private_zones = render_zone_stmt(root_domain.name, "private",
                CHROOT_ZONE_PATH + private_file_path)
    else:
        master_private_zones = ""
        slave_private_zones = ""
        DEBUG_STRING += "; NO PRIVATE ZONE DATA\n"

    if public_data:
        DEBUG_STRING += ";{0} {1} View Data {0}\n".format("=" * 30, "Public")
        DEBUG_STRING += soa_data
        DEBUG_STRING += public_data

        master_public_zones = render_zone_stmt(root_domain.name, "master",
                CHROOT_ZONE_PATH + public_file_path)
        slave_public_zones = render_zone_stmt(root_domain.name, "public",
                CHROOT_ZONE_PATH + public_file_path)
    else:
        master_public_zones = ""
        slave_public_zones = ""
        DEBUG_STRING += "; NO PUBLIC ZONE DATA\n"


    return ((master_public_zones, master_private_zones),
            (master_private_zones, slave_private_zones),
            DEBUG_STRING)

def build_zone_data(root_domain, soa):
    """
    This function does the heavy lifting of building a zone. It coordinates
    getting all of the data out of the db into BIND format.

    :param soa: The SOA corresponding to the zone being built.
    :type soa: SOA

    :param root_domain: The root domain of this zone.
    :type root_domain: str

    :returns public_file_path: The path to the zone file in the STAGEING dir
    :type public_file_path: str
    :returns public_data: The data that should be written to public_file_path
    :type public_data: str

    :returns private_zone_file: The path to the zone file in the STAGEING dir
    :type private_zone_file: str
    :param private_data: The data that should be written to private_zone_file
    :type private_data: str
    """
    ztype = 'reverse' if root_domain.is_reverse else 'forward'

    domains = soa.domain_set.all().order_by('name')

    DEBUG_STRING = ""
    # Bulid the mega filter!
    domain_mega_filter = Q(domain=root_domain)
    for domain in domains:
        domain_mega_filter = domain_mega_filter | Q(domain=domain)
    rdomain_mega_filter = Q(reverse_domain=root_domain)
    for reverse_domain in domains:
        rdomain_mega_filter = rdomain_mega_filter | Q(
                                            reverse_domain=reverse_domain)

    soa_data = render_soa_only(soa=soa, root_domain=root_domain)
    try:
        private = View.objects.get(name="private")
        if ztype == "forward":
            private_data = render_forward_zone(private, domain_mega_filter)
        else:
            private_data = render_reverse_zone(private, domain_mega_filter,
                                               rdomain_mega_filter)
    except ObjectDoesNotExist, e:
        private_data = ""

    try:
        public = View.objects.get(name="public")
        if ztype == "forward":
            public_data = render_forward_zone(public, domain_mega_filter)
        else:
            public_data = render_reverse_zone(public, domain_mega_filter,
                                              rdomain_mega_filter)
    except ObjectDoesNotExist, e:
        public_data = ""

    if private_data:
        private_data = soa_data + private_data

    if public_data:
        public_data = soa_data + public_data

    return (private_data, public_data)


def build_dns():
    master_public_zones = ""
    master_private_zones = ""

    slave_public_zones = ""
    slave_private_zones = ""

    for soa in SOA.objects.all().order_by("description"):
        root_domain = find_root_domain(soa)
        if not root_domain:
            print ("Couldn't find root domain. No zone statement was printed "
                "for {0}".format(soa))
            continue
        if root_domain.is_reverse:
            masters, slaves, _ =  build_zone("reverse", soa, root_domain)
        else:
            masters, slaves, _ =  build_zone("forward", soa, root_domain)
        tmp_m_pub_zs, tmp_m_pri_zs = masters
        master_public_zones += tmp_m_pub_zs
        master_private_zones += tmp_m_pri_zs

        tmp_s_pub_zs, tmp_s_pri_zs = slaves
        slave_public_zones += tmp_s_pub_zs
        slave_private_zones += tmp_s_pri_zs

    config_path = BUILD_PATH + "config/"
    if not os.access(config_path, os.R_OK):
        os.makedirs(config_path)

    with open(config_path + "master_public_zones", "w+") as fd:
        fd.write(master_public_zones)
    with open(config_path + "slave_public_zones", "w+") as fd:
        fd.write(slave_public_zones)

    with open(config_path + "master_private_zones", "w+") as fd:
        fd.write(master_private_zones)
    with open(config_path + "slave_private_zones", "w+") as fd:
        fd.write(slave_private_zones)
