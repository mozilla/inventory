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
