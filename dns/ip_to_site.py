from truth import Truth


def get_site_from_ip(ip, mappings):
    """
    Return a sites representation to be used in a hostname.

    :param ip: The ip to be used when determining the site.
    :type ip: str
    :param mappings: The data to use to determine which site an Ip belongs in.
    :type mappings: tuple
    :return site: The site's name
    :type site: str
    """
