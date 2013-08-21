__import__('inventory_context')
from django.db.models import Q

from systems.models import System
from systems.models import KeyValue
from systems.models import SystemStatus
from core.search.compiler.django_compile import compile_to_django


decomm = SystemStatus.objects.get(status='decommissioned')

system_map = [False] * System.objects.all().order_by('-pk')[0].pk


def mark_systems(search, key, value, extra=None):
    print ""
    print "-----------------------------------"
    print "Systems getting Key: {0} Value: {1}".format(key, value)
    systems = compile_to_django(search)[0]['SYS'].filter(
        ~Q(system_status=decomm)
    )

    for s in systems:
        if extra:
            extra(s, key, value)
        else:
            print s.hostname
            system_map[s.pk] = True
            KeyValue.objects.get_or_create(obj=s, key=key, value=value)


search_decomm = "(talos-r3 OR linux64-ix-slave OR linux-ix-slave OR releng-puppet OR buildbot-master) AND scl1 AND type=:sys"  # noqa
mark_systems(search_decomm, 'decomm.scl1', 'decommission')

search_migrate = "(talos-r4 OR EDID OR panda OR foopy OR mobile-imaging) AND scl1 AND type=:sys"  # noqa
mark_systems(search_migrate, 'decomm.scl1', 'migrate')

search_ = "(bld-centos6-hp OR bld-linux64-ix OR w64-ix) AND scl1 AND type=:sys"  # noqa
mark_systems(search_, 'decomm.scl1', 'replace')

search_ = "/scl1.mozilla.(com|net|org) type=:sys"  # noqa


def add_tbd(system, key, value):
    if system_map[system.pk]:
        return
    print system.hostname
    system_map[system.pk] = True  # redundant
    KeyValue.objects.get_or_create(obj=system, key=key, value=value)

mark_systems(search_, 'decomm.scl1', 'tbd', extra=add_tbd)
