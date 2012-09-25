from django.db.models import Q
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist

from mozdns.soa.models import SOA
from mozdns.validation import find_root_domain
from mozdns.mozbind.generators.bind_domain_generator import render_zone
from mozdns.mozbind.generators.bind_soa_generator import render_soa, render_soa_only
from mozdns.mozbind.generators.bind_reverse_domain_generator import render_reverse_domain
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
DEFAULT_TTL = 999

# DEBUG OPTIONS
DEBUG = True
DEBUG_BUILD_STRING = ''  # A string to store build output in.
CHROOT_ZONE_PATH = "/etc/invzones/"


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
    data = render_zone(
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


def render_reverse_zone(view, forward_mega_filter, reverse_mega_filter):
    data = render_reverse_domain(
            default_ttl=DEFAULT_TTL,

            nameserver_set=Nameserver.objects.filter(forward_mega_filter
                ).filter(views__name=view.name).order_by('server'),

            interface_set=StaticInterface.objects.filter(reverse_mega_filter,
                dns_enabled=True).filter(views__name=view.name).order_by(
                    'ip_type', 'label', 'ip_upper', 'ip_lower'),

            ptr_set=PTR.objects.filter(reverse_mega_filter).filter(views__name=view.name
                ).order_by('ip_upper').order_by( 'ip_lower'),

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


def build_zone(ztype, soa, root_domain):
    """This is where the magic happens.
    """
    soa.serial += 1
    # We are updating the local version of the soa. If this function succeeds
    # we will then save the SOA to the db.
    domains = soa.domain_set.all().order_by('name')
    zone_path = choose_zone_path(soa, root_domain)

    DEBUG_STRING = ""
    # Bulid the mega filter!
    forward_mega_filter = Q(domain=root_domain)
    for domain in domains:
        forward_mega_filter = forward_mega_filter | Q(domain=domain)
    reverse_mega_filter = Q(reverse_domain=root_domain)
    for reverse_domain in domains:
        reverse_mega_filter = reverse_mega_filter | Q(reverse_domain=reverse_domain)

    soa_data = render_soa_only(soa=soa, root_domain=root_domain)
    try:
        public = View.objects.get(name="public")
        if ztype == "forward":
            public_data = render_forward_zone(public, forward_mega_filter)
            public_file_path = zone_path + "public"
        else:
            public_data = render_reverse_zone(public, forward_mega_filter,
                    reverse_mega_filter)
            public_file_path = zone_path + root_domain.name + ".public"
    except ObjectDoesNotExist, e:
        data = "; The views public and private do not exist\n"
        public_data = ""
    try:
        private = View.objects.get(name="private")
        if ztype == "forward":
            private_data = render_forward_zone(private, forward_mega_filter)
            private_file_path = zone_path + "private"
        else:
            private_data = render_reverse_zone(private, forward_mega_filter,
                    reverse_mega_filter)
            private_file_path = zone_path + root_domain.name + ".private"
    except ObjectDoesNotExist, e:
        data = "; The views public and private do not exist\n"
        private_data = ""

    if not os.access(BUILD_PATH + zone_path, os.R_OK):
        os.makedirs(BUILD_PATH + zone_path)
    if private_data:
        open(BUILD_PATH + private_file_path, "w+").write(soa_data + private_data)
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
        open(BUILD_PATH + public_file_path, "w+").write(soa_data + public_data)
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

    # We made it. Let's save the SOA to the db now.
    soa.dirty = False
    soa.save()

    return ((master_public_zones, master_private_zones),
            (master_private_zones, slave_private_zones),
            DEBUG_STRING)

def build_dns():
    master_public_zones = ""
    master_private_zones = ""

    slave_public_zones = ""
    slave_private_zones = ""

    for soa in SOA.objects.all().order_by("comment"):
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
