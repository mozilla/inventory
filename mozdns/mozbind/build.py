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

from settings.local import BUILD_PATH
DEFAULT_TTL = 999

# DEBUG OPTIONS
DEBUG = True
DEBUG_BUILD_STRING = ''  # A string to store build output in.
CHROOT_ZONE_PATH = "/etc/named/invzones"


def render_reverse_zone(soa, root_domain, NOWRITE=False):
    domains = soa.domain_set.all().order_by('name')
    data = ""
    for domain in domains:
        data = render_soa_only(soa=soa, root_domain=root_domain)
        data += render_reverse_domain(
                default_ttl=DEFAULT_TTL,

                nameserver_set=domain.nameserver_set.all().order_by('server'),

                interface_set=domain.staticintrdomain_set.filter(
                    dns_enabled=True).order_by('ip_type', 'label', 'ip_upper',
                    'ip_lower'),

                ptr_set=domain.ptr_set.all().order_by('ip_upper').order_by(
                    'ip_lower'),

            )
    return data


def choose_zone_path(soa, root_domain, base_path):
    """This function decides where a zone's zone files go. If there is a key in
    the zone's KeyValue store called 'zone_path', that path is used. The path
    contained in 'zone_path' must exist on the file system.

    If no zone_path key is found. The following path is used:

        * Find the root domain of the zone (the one in the SOA record)
        * Replace all '.' characters with '/' characters.

    The build scripts will create this path on the filesystem if it does not
    exist.

    .. note::
        In all cases the zone_path is prepended with the ``BUILD_PATH`` varable
        found in ``settings/base.py``
    """
    soa.update_attrs()
    zone_path = None
    try:
        zone_path = soa.attrs.dir_path
    except AttributeError, e:
        tmp_path = '/'.join(reversed(root_domain.name.split('.')))
        zone_path = base_path + '/' + tmp_path + '/'
    return zone_path

def render_view(view, mega_filter):
    data = render_zone(
            default_ttl=DEFAULT_TTL,

            nameserver_set=view.nameserver_set.filter(mega_filter,
                ).order_by('server'),

            mx_set=view.mx_set.filter(mega_filter).order_by('server'),

            addressrecord_set=view.addressrecord_set.filter(mega_filter,
                ).order_by('ip_type', 'label', 'ip_upper', 'ip_lower'),

            interface_set=view.staticinterface_set.filter(mega_filter,
                dns_enabled=True).order_by('ip_type', 'label', 'ip_upper',
                'ip_lower'),

            cname_set=view.cname_set.filter(mega_filter).order_by(
                'label'),

            srv_set=view.srv_set.filter(mega_filter).order_by(
                'label'),

            txt_set=view.txt_set.filter(mega_filter).order_by(
                'label'),

            sshfp_set=view.sshfp_set.filter(mega_filter).order_by(
                'label'),
        )
    return data

def gen_moz_forward_zone(soa, root_domain, NOWRITE=False):
    domains = soa.domain_set.all().order_by('name')
    zone_path = choose_zone_path(soa, root_domain, BUILD_PATH)

    DEBUG_STRING = ""
    # Bulid the mega filter!
    mega_filter = Q(domain=root_domain)
    for domain in domains:
        mega_filter = mega_filter | Q(domain=domain)

    soa_data = render_soa_only(soa=soa, root_domain=root_domain)
    try:
        public = View.objects.get(name="public")
        public_data = render_view(public, mega_filter)
        public_file_path = zone_path + public.name
    except ObjectDoesNotExist, e:
        data = "; The views public and private do not exist"
    try:
        private = View.objects.get(name="private")
        private_data = render_view(private, mega_filter)
        private_file_path = zone_path + private.name
    except ObjectDoesNotExist, e:
        data = "; The views public and private do not exist"

    if not NOWRITE:
        if not os.access(zone_path, os.R_OK):
            os.makedirs(zone_path)
        open(private_file_path, "w+").write(soa_data + private_data
                + public_data)
        open(public_file_path, "w+").write(soa_data + private_data)
    if DEBUG:
        DEBUG_STRING += "%s File: %s %s \n%s\n" % ("=" * 20, private_file_path,
                "=" * 20, soa_data + public_data + private_data)
        DEBUG_STRING += "%s File: %s %s \n%s\n" % ("=" * 20, public_file_path,
                "=" * 20, soa_data + public_data)
    return DEBUG_STRING


def render_zone_stmt(zone_name, ns_type, file_path):
    zone_stmt = "\tzone \"{0}\" IN {{\n".format(zone_name)
    zone_stmt += "\t\ttype {0}\n".format(ns_type)
    zone_stmt += "\t\tfile \"{0}\"\n".format(file_path)
    zone_stmt += "\t}\n"
    return zone_stmt

def build_forward_zone_files():
    DEBUG_STRING = ''
    master_public_zones = ""
    master_private_zones = ""

    slave_public_zones = ""
    slave_private_zones = ""
    for soa in SOA.objects.all():
        root_domain = find_root_domain(soa)
        if not root_domain:
            #pdb.set_trace()
            continue
        if root_domain.is_reverse:
            continue
        print soa
        DEBUG_STRING += gen_moz_forward_zone(soa, root_domain)

        master_public_zone_stmt = render_zone_stmt(root_domain.name, "master",
                CHROOT_ZONE_PATH + "/master_forward_public")
        master_private_zone_stmt = render_zone_stmt(root_domain.name, "master",
                CHROOT_ZONE_PATH + "/master_forward_private")

        master_public_zones += master_public_zone_stmt
        master_private_zones += master_private_zone_stmt

        slave_public_zone_stmt = render_zone_stmt(root_domain.name, "private",
                CHROOT_ZONE_PATH + "/slave_forward_public")
        slave_private_zone_stmt = render_zone_stmt(root_domain.name, "private",
                CHROOT_ZONE_PATH + "/slave_forward_private")

        slave_public_zones += slave_public_zone_stmt
        slave_private_zones += slave_private_zone_stmt


    config_path = BUILD_PATH + "/config/"
    if not os.access(config_path, os.R_OK):
        os.makedirs(config_path)
    open(config_path+"master_forward_public", "w+").write(master_public_zones)
    open(config_path+"master_forward_private", "w+").write(master_private_zones)

    open(config_path+"slave_forward_public", "w+").write(master_public_zones)
    open(config_path+"slave_forward_private", "w+").write(master_private_zones)

    return DEBUG_STRING


def build_reverse_zone_files():
    DEBUG_STRING = ''
    master_public_zones = ""
    master_private_zones = ""

    slave_public_zones = ""
    slave_private_zones = ""

    for soa in SOA.objects.all():
        root_domain = find_root_domain(soa)
        DEBUG_STRING += gen_moz_reverse_zone(soa, root_domain)

        if root_domain.name.endswith('10.in-addr.arpa'):
            zone_path = BUILD_PATH + "/reverse/in-addr/10/"
            is_private = True
        elif root_domain.name.endswith('63.in-addr.arpa'):
            zone_path = BUILD_PATH + "/reverse/in-addr/63/"
            is_private = False
        if is_private:
            master_public_zone_stmt = render_zone_stmt(root_domain.name, "master",
                    CHROOT_ZONE_PATH + "/master_reverse_public")
            master_public_zones += master_public_zone_stmt

            slave_public_zone_stmt = render_zone_stmt(root_domain.name, "private",
                    CHROOT_ZONE_PATH + "/slave_forward_public")
            slave_public_zones += slave_public_zone_stmt

        master_private_zone_stmt = render_zone_stmt(root_domain.name, "master",
                CHROOT_ZONE_PATH + "/master_reverse_private")
        master_private_zones += master_private_zone_stmt

        slave_private_zone_stmt = render_zone_stmt(root_domain.name, "private",
                CHROOT_ZONE_PATH + "/slave_forward_private")
        slave_private_zones += slave_private_zone_stmt


    config_path = BUILD_PATH + "/config/"
    if not os.access(config_path, os.R_OK):
        os.makedirs(config_path)
    open(config_path+"master_reverse_public", "w+").write(master_public_zones)
    open(config_path+"master_reverse_private", "w+").write(master_private_zones)

    open(config_path+"slave_reverse_public", "w+").write(master_public_zones)
    open(config_path+"slave_reverse_private", "w+").write(master_private_zones)

    return DEBUG_STRING


def build_dns(*args, **kwargs):
    DEBUG_STRING = build_forward_zone_files()

    DEBUG_STRING += build_reverse_zone_files()

    return DEBUG_STRING

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

def is_reverse_private(domain):
    """Look at a :ref:`domain` and determine if it is private i.e. it's name
    ends with '10.in-addr.arpa'
    """
    if root_domain.name.endswith('10.in-addr.arpa'):
        zone_path = BUILD_PATH + "/reverse/in-addr/10/"
        is_private = True
    elif root_domain.name.endswith('63.in-addr.arpa'):
        zone_path = BUILD_PATH + "/reverse/in-addr/63/"
        is_private = False
    return is_private

def build_reverse_domain(soa, root_domain):
    master_public_zones = ""
    master_private_zones = ""

    slave_public_zones = ""
    slave_private_zones = ""

    private = is_reverse_private(root_domain)
    if private:
        # Part 1.reverse --> file in /in-addr/private
        rel_dir_path = "/reverse/in-addr/private/"
        rel_zone_path = rel_dir_path + "db.{0}".format(
                root_domain.name)
        output = render_reverse_zone(soa, root_domain)
        data_path = BUILD_PATH + rel_dir_path
        if not os.access(data_path, os.R_OK):
            os.makedirs(data_path)
        with open(private_file_path, "w+") as fd:
            fd.write(output)

    else:  # public reverse zone
        # Part 1.reverse --> file in /in-addr/public
        output = render_reverse_zone(soa, root_domain)
        rel_dir_path = "/reverse/in-addr/public/"
        rel_zone_path = rel_dir_path + "db.{0}".format(
                root_domain.name)
        rel_zone_path = rel_dir_path + "db.{0}".format(
                root_domain.name)
        output = output_private_reverse(soa, root_domain)
        data_path = BUILD_PATH + rel_dir_path
        if not os.access(data_path, os.R_OK):
            os.makedirs(data_path)
        with open(private_file_path, "w+") as fd:
            fd.write(output)

        # Only public get's into public
        # Part 2.public
        master_public_zones += render_zone_stmt(root_domain.name,
                "master", CHROOT_ZONE_PATH + "/" + rel_zone_path)

        slave_public_zones += render_zone_stmt(root_domain.name,
                "slave", CHROOT_ZONE_PATH + "/" + rel_zone_path)

    # Both public and private go into private
    # Part 2.private
    master_private_zones += render_zone_stmt(root_domain.name, "master",
            CHROOT_ZONE_PATH + "/private/db.{0}".format(rel_zone_path))

    slave_private_zones += render_zone_stmt(root_domain.name, "slave",
            CHROOT_ZONE_PATH + "/private/db.{0}".format(rel_zone_path))

    return ((master_public_zones, master_private_zones),
            (master_private_zones, slave_private_zones))

def build_forward_domain(soa, root_domain):
    """
    Things every zone needs:
        1) data file's
            1.forward) Forward needs private and reverse
            1.reverse) Reverse needs one in /in-addr/private or /in-addr/public
        2) An zone entry in public and/or private named.conf include
            2.public) public get's a statement in public and private includes
            2.private) public get's a statement in only private includes
    """
    domains = soa.domain_set.all().order_by('name')
    zone_path = choose_zone_path(soa, root_domain, BUILD_PATH)

    DEBUG_STRING = ""
    # Bulid the mega filter!
    mega_filter = Q(domain=root_domain)
    for domain in domains:
        mega_filter = mega_filter | Q(domain=domain)

    soa_data = render_soa_only(soa=soa, root_domain=root_domain)
    try:
        public = View.objects.get(name="public")
        public_data = render_view(public, mega_filter)
        public_file_path = zone_path + public.name
    except ObjectDoesNotExist, e:
        data = "; The views public and private do not exist"
    try:
        private = View.objects.get(name="private")
        private_data = render_view(private, mega_filter)
        private_file_path = zone_path + private.name
    except ObjectDoesNotExist, e:
        data = "; The views public and private do not exist"

    if not os.access(zone_path, os.R_OK):
        os.makedirs(zone_path)
    open(private_file_path, "w+").write(soa_data + private_data
            + public_data)
    open(public_file_path, "w+").write(soa_data + private_data)

    master_public_zones = render_zone_stmt(root_domain.name, "master",
            choose_zone_path(soa, root_domain, CHROOT_ZONE_PATH))
    master_private_zones = render_zone_stmt(root_domain.name, "master",
            choose_zone_path(soa, root_domain, CHROOT_ZONE_PATH))

    slave_public_zones = render_zone_stmt(root_domain.name, "private",
            choose_zone_path(soa, root_domain, CHROOT_ZONE_PATH))
    slave_private_zones = render_zone_stmt(root_domain.name, "private",
            choose_zone_path(soa, root_domain, CHROOT_ZONE_PATH))

    return ((master_public_zones, master_private_zones),
            (master_private_zones, slave_private_zones))

def build_dns():
    """
    Things every zone needs:
        1) data file's
            1.forward) Forward needs private and reverse
            1.reverse) Reverse needs one in /in-addr/private or /in-addr/public
        2) An zone entry in public and/or private named.conf include
            2.public) public get's a statement in public and private includes
            2.private) public get's a statement in only private includes
    """
    master_public_zones = ""
    master_private_zones = ""

    slave_public_zones = ""
    slave_private_zones = ""

    for soa in soa.objects.all().order_by("comment"):
        root_domain = find_root_domain(soa)
        if root_domain.is_reverse:
            masters, slaves =  build_reverse_domain(soa, root_domain)
            tmp_m_pub_zs, tmp_m_pri_zs = masters
            master_public_zones += tmp_m_pub_zs
            master_private_zones += tmp_m_pri_zs

            tmp_s_pub_zs, tmp_s_pri_zs = slaves
            slave_public_zones += tmp_s_pub_zs
            slave_private_zones += tmp_s_pri_zs
        else:
            masters, slaves =  build_forward_domain(soa, root_domain)
            tmp_m_pub_zs, tmp_m_pri_zs = masters
            master_public_zones += tmp_m_pub_zs
            master_private_zones += tmp_m_pri_zs

            tmp_s_pub_zs, tmp_s_pri_zs = slaves
            slave_public_zones += tmp_s_pub_zs
            slave_private_zones += tmp_s_pri_zs
