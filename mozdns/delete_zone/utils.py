from django.core.exceptions import ValidationError

from core.search.compiler.django_compile import compile_to_django


def delete_zone_helper(domain_name):
    if not domain_name:
        return {
            'success': False,
            'message': 'Which zone do you want to delete?'
        }
    if domain_name in ('mozilla.com', 'mozilla.net', 'mozilla.org',
                       'allizom.org'):
        raise ValidationError('Go home.')

    zone_objs = compile_to_django("zone=:{0}".format(domain_name))

    rdtypes = ('CNAME', 'MX', 'A', 'SRV', 'PTR', 'SSHFP', 'NS', 'TXT', 'SREG')
    for rdtype in rdtypes:
        zone_objs[0][rdtype].delete()

    soa = zone_objs[0]['SOA'][0]
    root_domain = soa.root_domain

    def maybe_delete_domain(d):
        domain_status = []
        for cd in d.domain_set.all():
            if cd.soa == soa:
                domain_status.append(maybe_delete_domain(cd))
            else:
                domain_status.append(False)

        if reduce(lambda x, y: x and y, domain_status, True):
            d.delete()
            return True
        else:
            d.soa = None
            d.save()
            return False

    maybe_delete_domain(root_domain)
    soa.delete()
    return {'success': True, 'message': 'success'}
