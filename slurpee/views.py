import MySQLdb

from django.shortcuts import render

from core.search.compiler.django_compile import search_type
from slurpee.constants import P_OVERLAY


def conflict_attrs(s):
    return s.externaldata_set.filter(policy=P_OVERLAY)


def get_conflicts(s):
    conflicts = []
    for ed in conflict_attrs(s):
        if s.external_data_conflict(ed.name):
            conflicts.append(ed)
    return conflicts


def show_conflicts(request):
    """
    This view is temporary. It can be used to convert a system using KV objects
    for dhcp into the new Sreg and HW scheme.
    """
    if request.GET:
        search = request.GET.get('search', '')
        records, error = search_type(search, 'SYS')
        try:
            total = records.count()
            records = records
        except MySQLdb.OperationalError, e:
            if "Got error " in str(e) and " from regexp" in str(e):
                # This is nasty. If the user is using an invalid regex
                # patter, the db might shit a brick
                total = 0
                records = []
            else:
                raise

        return render(request, 'slurpee/conflicts.html', {
            'search': search,
            'total': total,
            'records': records,
            'get_conflicts': get_conflicts,
            'getattr': getattr
        })
    else:
        return render(request, 'slurpee/conflicts.html', {
            'search': '',
            'total': 0
        })
