from django.db.models import Q

from mozdns.address_record.models import AddressRecord
from mozdns.cname.models import CNAME
from mozdns.mx.models import MX
from mozdns.nameserver.models import Nameserver
from mozdns.ptr.models import PTR
from mozdns.srv.models import SRV
from mozdns.txt.models import TXT
from mozdns.sshfp.models import SSHFP
from mozdns.view.models import View
from core.interface.static_intr.models import StaticInterface

from gettext import gettext as _
from core.utils import fail_mail

DEFAULT_TTL = 3600


def render_soa_only(soa, root_domain):
    BUILD_STR = _("{root_domain}.  {ttl}  IN   SOA   {primary}. {contact}. (\n"
                  "\t\t{{serial}}     ; Serial\n"
                  "\t\t{refresh}     ; Refresh\n"
                  "\t\t{retry}     ; Retry\n"
                  "\t\t{expire}     ; Expire\n"
                  "\t\t{minimum}     ; Minimum\n"
                  ")\n\n".format(
                      ttl=soa.ttl,
                      root_domain=root_domain.name, primary=soa.primary,
                      contact=soa.contact, refresh=str(soa.refresh),
                      retry=str(soa.retry), expire=str(soa.expire),
                      minimum=soa.minimum))
    return BUILD_STR


def render_rdtype(rdtype_set, **kwargs):
    BUILD_STR = ""
    for obj in rdtype_set:
        BUILD_STR += _(obj.bind_render_record(**kwargs) + "\n")
    return BUILD_STR


def _render_forward_zone(default_ttl, nameserver_set, mx_set,
                         addressrecord_set, interface_set, cname_set, srv_set,
                         txt_set, sshfp_set):
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


def render_forward_zone(view, mega_filter):
    data = _render_forward_zone(
        default_ttl=DEFAULT_TTL,

        nameserver_set=Nameserver.objects.filter(mega_filter).filter(
            views__name=view.name).order_by('server'),

        mx_set=MX.objects.filter(mega_filter).filter(views__name=view.name
                                                     ).order_by('server'),

        addressrecord_set=AddressRecord.objects.filter(mega_filter).filter(
            views__name=view.name).order_by('pk', 'ip_type', 'fqdn',
                                            'ip_upper', 'ip_lower'),

        interface_set=StaticInterface.objects.filter(
            mega_filter, dns_enabled=True).filter(
                views__name=view.name).order_by('pk', 'ip_type', 'fqdn',
                                                'ip_upper', 'ip_lower'),

        cname_set=CNAME.objects.filter(mega_filter).filter(
            views__name=view.name).order_by('fqdn'),

        srv_set=SRV.objects.filter(mega_filter).filter(views__name=view.name
                                                       ).order_by(
                                                           'pk', 'fqdn'),

        txt_set=TXT.objects.filter(mega_filter).filter(views__name=view.name
                                                       ).order_by(
                                                           'pk', 'fqdn'),

        sshfp_set=SSHFP.objects.filter(mega_filter).filter(
            views__name=view.name).order_by('pk', 'fqdn'),
    )
    return data


def _render_reverse_zone(default_ttl, nameserver_set, interface_set, ptr_set):
    BUILD_STR = ''
    BUILD_STR += render_rdtype(nameserver_set)
    BUILD_STR += render_rdtype(ptr_set)
    BUILD_STR += render_rdtype(interface_set, reverse=True, rdtype='PTR')
    return BUILD_STR


def render_reverse_zone(view, domain_mega_filter, rdomain_mega_filter):
    data = _render_reverse_zone(
        default_ttl=DEFAULT_TTL,

        nameserver_set=Nameserver.objects.filter(domain_mega_filter).filter(
            views__name=view.name).order_by('server'),

        interface_set=StaticInterface.objects.filter(
            rdomain_mega_filter, dns_enabled=True).filter(
                views__name=view.name).order_by(
                    'pk', 'ip_type', 'label', 'ip_upper', 'ip_lower'),

        ptr_set=PTR.objects.filter(rdomain_mega_filter).filter(
            views__name=view.name).order_by('pk', 'ip_upper',
                                            'ip_lower'),

    )
    return data


def build_zone_data(view, root_domain, soa, logf=None):
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

    :returns view_zone_file: The path to the zone file in the STAGEING dir
    :type view_zone_file: str
    :param view_data: The data that should be written to view_zone_file
    :type view_data: str
    """
    ztype = 'reverse' if root_domain.is_reverse else 'forward'
    if (soa.has_record_set(view=view, exclude_ns=True) and
            not root_domain.nameserver_set.filter(views=view).exists()):
        msg = ("The {0} zone has a records in the {1} view, but there are "
               "no nameservers in that view. A zone file for {1} won't be "
               "built. Use the search string 'zone=:{0} view=:{1}' to find "
               "the troublesome records".format(root_domain, view.name))
        fail_mail(msg, subject="Shitty edge case detected.")
        logf('LOG_WARNING', msg)
        return ''

    domains = soa.domain_set.all().order_by('name')

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
        if ztype == "forward":
            view_data = render_forward_zone(view, domain_mega_filter)
        else:
            view_data = render_reverse_zone(view, domain_mega_filter,
                                            rdomain_mega_filter)
    except View.DoesNotExist:
        view_data = ""

    if view_data:
        view_data = soa_data + view_data

    return view_data
