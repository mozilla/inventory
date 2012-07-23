import mozdns
import core
import pdb
from django.db.models import Q


def fqdn_search(fqdn, *args, **kwargs):
    """Find any records that have a name that is the provided fqdn. This
    name would show up on the left hand side of a zone file and in a PTR's
    case the right side.

    :param fqdn: The name to search for.
    :type   fqdn: str
    :return: (type, Querysets) tuples containing all the objects that matched
        during
    the search are returned.
    """
    return _build_queries(fqdn, *args, **kwargs)


def fqdn_exists(fqdn, **kwargs):
    """Return a Queryset or False depending on whether an object exists
    with the fqdn.

    :param fqdn: The name to search for.
    :type   fqdn: str
    :return: True or False
    """
    for type_, qset in _build_queries(fqdn, **kwargs):
        if qset.exists():
            return qset
    return False


def _build_queries(fqdn, dn=True, mx=True, sr=True, tx=True,
                    cn=True, ar=True, pt=True, ip=False, intr=True,
                    search_operator=''):
    # We import this way to make it easier to import this file without
    # getting cyclic imports.
    qsets = []
    if dn:
        qsets.append(('Domain', mozdns.domain.models.Domain.objects.
            filter(**{'name{0}'.format(search_operator): fqdn})))
    if mx:
        qsets.append(('MX', mozdns.mx.models.MX.objects.
            filter(**{'fqdn{0}'.format(search_operator): fqdn})))
    if sr:
        qsets.append(('SRV', mozdns.srv.models.SRV.objects.
            filter(**{'fqdn{0}'.format(search_operator): fqdn})))
    if tx:
        qsets.append(('TXT', mozdns.txt.models.TXT.objects.
            filter(**{'fqdn{0}'.format(search_operator): fqdn})))
    if cn:
        qsets.append(('CNAME', mozdns.cname.models.CNAME.objects.
            filter(**{'fqdn{0}'.format(search_operator): fqdn})))
    if ar:
        AddressRecord = mozdns.address_record.models.AddressRecord
        ars = AddressRecord.objects.filter(Q(fqdn=fqdn) | Q(ip_str=ip))
        qsets.append(('AddressRecord', ars))
    if pt:
        qsets.append(('PTR', mozdns.ptr.models.PTR.objects.
            Q(**{'name{0}'.format(search_operator): fqdn}) |
            Q(**{'ip_str{0}'.format(search_operator): ip})))
    if intr:
        StaticInterface = core.interface.static_intr.models.StaticInterface
        qsets.append(('StaticInterface', StaticInterface.objects.filter(
            Q(**{'fqdn{0}'.format(search_operator): fqdn}) |
            Q(**{'ip_str{0}'.format(search_operator): ip}))))

    return qsets
