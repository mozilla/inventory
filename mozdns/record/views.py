import MySQLdb
import simplejson as json

from django.shortcuts import render
from django.http import HttpResponse
from django.http import Http404
from django.core.exceptions import ValidationError

from mozdns.domain.models import Domain
from core.search.compiler.django_compile import search_type
from core.utils import locked_function

from mozdns.record.utils import get_obj_meta


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


def record_delete(request, record_type='', record_pk=''):
    if request.method != 'POST':
        raise Http404
    obj_meta = get_obj_meta(record_type)

    try:
        object_ = obj_meta.Klass.objects.get(pk=record_pk)
    except obj_meta.Klass.DoesNotExist:
        error = "Could not find that object."
        return HttpResponse(json.dumps({'success': False, 'error': error}))

    try:
        object_.delete()
    except ValidationError, e:
        error = e.messages[0]
        return HttpResponse(json.dumps({'success': False, 'error': error}))

    return HttpResponse(json.dumps({'success': True}))


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
    records, error = search_type(query, record_type)
    if error:
        total_obj_count = 0
        records = []
    else:
        try:
            total_obj_count = records.count()
            records = records[:50]
        except MySQLdb.OperationalError, e:
            if "Got error " in str(e) and " from regexp" in str(e):
                # This is nasty. If the user is using an invalid regex patter,
                # the db might shit a brick
                total_obj_count = 0
                records = []
            else:
                raise

    return render(request, 'record/record_search_results.html', {
        'query': "{0} AND type=:{1}".format(query, record_type),
        'objs': records,
        'record_type': record_type,
        'total_obj_count': total_obj_count
    })


def record_ajax(request):
    # This function is pretty much a router
    if request.method == 'POST':
        return _record_post(request)
    else:
        record_type = request.GET.get('record_type', '')
        record_pk = request.GET.get('record_pk', '')
        obj_meta = get_obj_meta(record_type)()
        return obj_meta.get(request, record_type, record_pk)


@locked_function('inventory.record_lock', 10)
def _record_post(request):
    record_type = request.POST.get('record_type', '')
    record_pk = request.POST.get('record_pk', '')
    obj_meta = get_obj_meta(record_type)()
    return obj_meta.post(request, record_type, record_pk)
