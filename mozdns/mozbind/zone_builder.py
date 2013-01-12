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
DEFAULT_TTL = 3600


def render_soa_only(soa, root_domain):
    BUILD_STR = "{root_domain}.     IN      SOA     {primary}. {contact}. (\n\
                            {{serial:20}}     ; Serial\n\
                            {refresh:20}     ; Refresh\n\
                            {retry:20}     ; Retry\n\
                            {expire:20}     ; Expire\n\
                            {minimum:20}     ; Minimum\n\
                )\n\n".format(root_domain=root_domain.name,
                              primary=soa.primary, contact=soa.contact,
                              refresh=str(soa.refresh), retry=str(soa.retry),
                              expire=str(soa.expire), minimum=soa.minimum)
    return BUILD_STR


def render_rdtype(rdtype_set, **kwargs):
    BUILD_STR = ""
    for obj in rdtype_set:
        BUILD_STR += _(obj.bind_render_record(**kwargs) + "\n")
    return BUILD_STR


def _render_forward_zone(default_ttl, nameserver_set, mx_set,
        addressrecord_set, interface_set, cname_set, srv_set, txt_set,
        sshfp_set):
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


def _render_reverse_zone(default_ttl, nameserver_set, interface_set, ptr_set):
    BUILD_STR = ''
    BUILD_STR += render_rdtype(nameserver_set)
    BUILD_STR += render_rdtype(ptr_set)
    BUILD_STR += render_rdtype(interface_set, reverse=True, rdtype='PTR')
    return BUILD_STR


def render_reverse_zone(view, domain_mega_filter, rdomain_mega_filter):
    data = _render_reverse_zone(
            default_ttl=DEFAULT_TTL,

            nameserver_set=Nameserver.objects.filter(domain_mega_filter
                ).filter(views__name=view.name).order_by('server'),

            interface_set=StaticInterface.objects.filter(rdomain_mega_filter,
                dns_enabled=True).filter(views__name=view.name).order_by(
                    'ip_type', 'label', 'ip_upper', 'ip_lower'),

            ptr_set=PTR.objects.filter(rdomain_mega_filter).filter(
                    views__name=view.name).order_by('ip_upper'
                    ).order_by('ip_lower'),

        )
    return data


def build_zone_data(root_domain, soa, logf=None):
    """
    This function does the heavy lifting of building a zone. It coordinates
    getting all of the data out of the db into BIND format.

    .. note::
        If a zone's root_domain does not have any :class:`Nameserver`
        object associated with it this function will not build zone data for
        that zone (BIND will fail if an NS record for a zone's root domain does
        not exist). This function will also log that it encountered this case.

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
    if not root_domain.nameserver_set.exists():
        if logf:
            logf('LOG_WARNING', "The SOA '{0}' has a root_domain of {1} which "
                    "doesn't have any nameservers. No attempt to build it's "
                    "zone files will be made built.".format(soa, root_domain),
                    soa=soa)
        return '', ''

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
        private = View.objects.get(name="private")
        if ztype == "forward":
            private_data = render_forward_zone(private, domain_mega_filter)
        else:
            private_data = render_reverse_zone(private, domain_mega_filter,
                                               rdomain_mega_filter)
    except View.DoesNotExist:
        private_data = ""

    try:
        public = View.objects.get(name="public")
        if ztype == "forward":
            public_data = render_forward_zone(public, domain_mega_filter)
        else:
            public_data = render_reverse_zone(public, domain_mega_filter,
                                              rdomain_mega_filter)
    except View.DoesNotExist:
        public_data = ""

    if private_data:
        private_data = soa_data + private_data

    if public_data:
        public_data = soa_data + public_data

    return (private_data, public_data)
