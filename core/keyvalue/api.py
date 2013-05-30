# Some nice RESTful endpoints
from django.http import HttpResponse
from django.core.exceptions import ValidationError
from core.keyvalue.views import resolve_obj, resolve_class


import simplejson as json


def get_kv(request):
    k, v = request.POST.get('key', None), request.POST.get('value', None)
    if not k:
        return None, None, 'Key is required'
    if not v:
        return None, None, 'Key is required'
    return k, v, None


def kv_detail(request, kv_class, kv_pk):
    """
    GET to:
    /core/keyvalue/api/<kv_class>/<kv_pk>/detail/

    Returns a single KV instance.
    """
    Klass = resolve_class(kv_class)
    KVKlass = Klass.keyvalue_set.related.model
    try:
        kv = KVKlass.objects.get(pk=kv_pk)
    except KVKlass.DoesNotExist:
        return HttpResponse(
            status=404, content=json.dumps({'success': False})
        )
    return HttpResponse(
        json.dumps(kv.get_bundle())
    )


def kv_list(request, kv_class, obj_pk):
    """
    GET to:
    /core/keyvalue/api/<kv_class>/<kv_pk>/list/

    Returns a list of all KV objects associated with an object.
    """
    obj, KVKlass = resolve_obj(kv_class, obj_pk)
    kvs = KVKlass.objects.filter(obj=obj)
    ret_kvs = []
    for kv in kvs:
        ret_kvs.append(kv.get_bundle())
    return HttpResponse(
        json.dumps({'success': True, 'kvs': ret_kvs})
    )


def kv_create(request, kv_class, obj_pk):
    """
    POST to:
    /core/keyvalue/api/<kv_class>/create/

    with parameters like:

    {
        'key': 'key_string'
        'value': 'value_string'
        'obj_pk': 1
    }

    Status Codes:
        * 201 - Object created
        * 400 - Issues during creation
    """
    key, value, errors = get_kv(request)
    if errors:
        return HttpResponse(
            status=400, content=json.dumps(
                {'success': False, 'message': errors}
            )
        )
    obj, KVKlass = resolve_obj(kv_class, obj_pk)
    try:
        kv = KVKlass(obj=obj, key=key, value=value)
        kv.clean()
        kv.save()
        resp = {
            'status': 201,
            'content': json.dumps(
                {
                    'success': True,
                    'key': kv.key,
                    'value': kv.value,
                    'obj_uri': kv.uri,
                    'kv_pk': kv.pk
                }
            )
        }
    except ValidationError, e:
        resp = {
            'status': 400,
            'content': json.dumps({'success': False, 'message': str(e)})
        }
    return HttpResponse(**resp)


def kv_update(request, kv_class, kv_pk):
    """
    POST to:
    /core/keyvalue/api/<kv_class>/<kv_pk>/update/

    with parameters like:

    {
        'key': 'key_string'
        'value': 'value_string'
        'obj_pk': 1
    }
    Status Codes:
        * 200 - Object updated
        * 400 - Issues during update
    """
    key, value, errors = get_kv(request)
    if errors:
        return HttpResponse(
            status=400, content=json.dumps(
                {'success': False, 'message': errors}
            )
        )
    Klass = resolve_class(kv_class)
    KVKlass = Klass.keyvalue_set.related.model
    try:
        kv = KVKlass.objects.get(pk=kv_pk)
    except KVKlass.DoesNotExist:
        return HttpResponse(
            status=404, content=json.dumps({'success': False})
        )
    try:
        kv.key = key
        kv.value = value
        kv.clean()
        kv.save()
        resp = {
            'status': 200,
            'content': json.dumps(
                {'success': True, 'key': kv.key, 'value': kv.value}
            )
        }
    except ValidationError, e:
        resp = {
            'status': 400,
            'content': json.dumps({'success': False, 'message': str(e)})
        }
    return HttpResponse(**resp)


def kv_delete(request, kv_class, kv_pk):
    """
    POST to:
    /core/keyvalue/api/<kv_class>/<kv_pk>/delete/
    Status Codes:
        * 204 - Requests Fulfilled
        * 400 - Issues during delete
    """
    Klass = resolve_class(kv_class)
    KVKlass = Klass.keyvalue_set.related.model
    try:
        kv = KVKlass.objects.get(pk=kv_pk)
    except KVKlass.DoesNotExist:
        return HttpResponse(
            status=404, content=json.dumps({'success': False})
        )
    kv.delete()
    return HttpResponse(
        status=204,
        content=json.dumps({'success': True})
    )
