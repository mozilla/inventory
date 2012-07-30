from django.db.models import Q

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

BUILD_PATH = "/home/juber/dnsbuilds"
DEFAULT_TTL = 999

# DEBUG OPTIONS
DEBUG = True
DEBUG_BUILD_STRING = ''  # A string to store build output in.


def gen_moz_reverse_zone(soa, NOWRITE=False):
    domains = soa.domain_set.all().order_by('name')
    root_domain = find_root_domain(soa)
    if not root_domain.is_reverse:  # Skip forward domains
        return ""
    # 22.8.10.in-addr.arpa -> '10.8.22'
    tmp_path = root_domain.name.replace('in-addr.arpa', '')
    rname = list(reversed(tmp_path.split('.')))
    tmp_path1 = '.'.join(rname[:3]).strip('.')
    tmp_path2 = '.'.join(rname).strip('.')
    DEBUG_STRING = ""

    zone_path = BUILD_PATH + '/in-addr/' + tmp_path1 + '/'
    file_path = zone_path + tmp_path2

    for domain in domains:
        data = render_soa_only(
                            soa=soa, root_domain=root_domain,
                         )
        data += render_reverse_domain(
                default_ttl=DEFAULT_TTL,

                nameserver_set=domain.nameserver_set.all().order_by('server'),

                interface_set=domain.staticintrdomain_set.filter(
                    dns_enabled=True).order_by('ip_type', 'label', 'ip_upper',
                    'ip_lower'),

                ptr_set=domain.ptr_set.all().order_by('ip_upper').order_by(
                    'ip_lower'),

            )
        if not NOWRITE:
            if not os.access(zone_path, os.R_OK):
                os.makedirs(zone_path)
            open(file_path, "w+").write(data)
        if DEBUG:
            DEBUG_STRING += "%s File: %s %s \n%s\n" % ("=" * 20, file_path,
                    "=" * 20, data)
    return DEBUG_STRING


def gen_moz_forward_zone(soa, NOWRITE=False):
    domains = soa.domain_set.all().order_by('name')
    root_domain = find_root_domain(soa)
    if root_domain.is_reverse:  # Skip reverse domains
        return ""
    if not root_domain.name.endswith('mozilla.com'):
        tmp_path = root_domain.name.replace('.', '/')
        tmp_path.strip('/')
    else:
        # Find the name which to create a directory under.
        # I.E. phx1.mozilla.com -> phx1/
        tmp_path = root_domain.name.replace('mozilla.com', '').replace('.', '/')
        tmp_path.strip('/')
    zone_path = BUILD_PATH + '/' + tmp_path
    DEBUG_STRING = ""
    # Bulid the mega filter!
    mega_filter = Q(domain=root_domain)
    for domain in domains:
        mega_filter = mega_filter | Q(domain=domain)

    for view in View.objects.all():
        file_path = zone_path + view.name
        data = render_soa_only(
                            soa=soa, root_domain=root_domain,
                    )
        data += render_zone(
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
        if not NOWRITE:
            if not os.access(zone_path, os.R_OK):
                os.makedirs(zone_path)
            open(file_path, "w+").write(data)
        if DEBUG:
            DEBUG_STRING += "%s File: %s %s \n%s\n" % ("=" * 20, file_path,
                    "=" * 20, data)
    return DEBUG_STRING


def build_forward_zone_files():
    DEBUG_STRING = ''
    for soa in SOA.objects.all():
        DEBUG_STRING += gen_moz_forward_zone(soa)
    return DEBUG_STRING


def build_reverse_zone_files():
    DEBUG_STRING = ''
    for soa in SOA.objects.all():
        DEBUG_STRING += gen_moz_reverse_zone(soa)
    return DEBUG_STRING


def build_dns(*args, **kwargs):
    DEBUG_STRING = build_forward_zone_files()

    DEBUG_STRING += build_reverse_zone_files()

    return DEBUG_STRING
