from mozdns.domain.models import Domain
from core.interface.static_intr.views import find_available_ip_from_ipv4_range
def get_available_ip_by_domain(domain):
    """
    :param domain: The domain to choose from
    :type domain: class:`Domain`
    :param system: The system the interface belongs to
    :returns: ip_address

    This function looks at `domain.name` and strips off 'mozilla.com' (yes it
    needs to be `<something>.mozilla.com`). The function then tries to
    determine which site and vlan the domain is in. Once it knows the site and
    vlan it looks for network's in the vlan and eventually for ranges and a
    free ip in that range. If at any time this function can't do any of those
    things it raises a ValidationError.
    """

    name = domain.name.replace('mozilla.com','')
    # First look for a site. This could be the first label or a combination of
    # labels.
    site_name = ""
    for label in reversed(name.split('.'):
        possible = Site.objects.filter(label)
        if possible:
            site = possible[0]
        site_name = label

def domain_to_site(domain):
    pass
