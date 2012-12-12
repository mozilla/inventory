import operator
import MySQLdb

from django.shortcuts import render
from django.db.models import Q
from django.forms.util import ErrorList, ErrorDict
from django.http import HttpResponse
from django.http import Http404

from mozdns.domain.models import Domain
from mozdns.utils import slim_form
from core.search.compiler.django_compile import search_type

from mozdns.record.utils import get_obj_meta

import simplejson as json

import pdb

def record_search(request, record_type=None):
    if not record_type:
        record_type = 'A'
    return render(request, 'record/record_search.html', {
        'record_type': record_type
    })

def record(request, record_type='', record_pk=''):
    domains = Domain.objects.filter(is_reverse=False)
    if not record_type:
        record_type = 'A'
    return render(request, 'record/record.html', {
        'record_type': record_type,
        'record_pk': record_pk,
        'domains': json.dumps([domain.name for domain in domains]),
    })

def record_search_ajax(request):
    """
    This function will return a list of records matching the 'query' of type
    'record_type'. It's used for ajaxy stuff.
    """
    query = request.GET.get('query', '')
    record_type = request.GET.get('record_type', '')
    obj_meta = get_obj_meta(record_type)
    if not record_type:
        raise Http404
    if not query and record_type:
        return render(request, 'record/record_search_results.html', {
            'objs': [],
            'record_type': record_type,
        })

    if not obj_meta.Klass:
        raise Http404
    mega_filter, error = search_type(query, record_type)
    if not mega_filter:
        records = []
    else:
        try:
            records = list(obj_meta.Klass.objects.filter(mega_filter)[:50])
        except MySQLdb.OperationalError, e:
            if "Got error " in str(e) and " from regexp" in str(e):
                # This is nasty. If the user is using an invalid regex patter,
                # the db might shit a brick
                records = []
            else:
                raise

    return render(request, 'record/record_search_results.html', {
        'objs': records,
        'record_type': record_type,
    })

def record_ajax(request):
    # This function is pretty much a router
    if request.method == 'POST':
        record_type = request.POST.get('record_type', '')
        record_pk = request.POST.get('record_pk', '')
        obj_meta = get_obj_meta(record_type)()
        return obj_meta.post(request, record_type, record_pk)
    else:
        record_type = request.GET.get('record_type', '')
        record_pk = request.GET.get('record_pk', '')
        obj_meta = get_obj_meta(record_type)()
        return obj_meta.get(request, record_type, record_pk)
