from inventory_context import *
from django.db.models import Q
from core.search.compiler.invfilter import searchables
from mozdns.soa.models import SOA


def fix_ttl_for_rdtype(manager):
    manager.objects.filter(Q(ttl=3600)).update(ttl=None)
    manager.objects.filter(Q(ttl=0)).update(ttl=None)

rdtypes = ('A', 'CNAME', 'NS', 'TXT', 'SRV', 'PTR', 'SRV', 'MX', 'SSHFP')

for s_rdtype, manager in searchables:
    if s_rdtype in rdtypes:
        fix_ttl_for_rdtype(manager)

for s in SOA.objects.all():
    s.minimum = 3600
    s.save()
