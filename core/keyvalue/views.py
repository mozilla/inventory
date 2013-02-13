from django.shortcuts import render
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.http import HttpResponse

from core.network.models import Network
from core.keyvalue.utils import get_aa

import simplejson as json


def process_kv(kv, KVClass):

    existing_kvs = []
    new_kvs = []
    for k, v in kv:
        if k.startswith('existing_v_'):
            existing_kv = KVClass.objects.get(pk=k.strip('existing_v_'))
            existing_kv.value = v
            existing_kvs.append(existing_kv)
        elif k.startswith('attr_new_key_'):
            k_num = k.strip('attr_new_key_')
            value_k_name = 'attr_new_value_' + k_num
            for ki, vi in kv:
                if ki == value_k_name:
                    new_kv = KVClass(key=v, value=vi)
                    new_kvs.append(new_kv)
    return_attrs = []
    for kv in existing_kvs:
        try:
            kv.clean()
            return_attrs.append((kv, None))
        except ValidationError, e:
            return_attrs.append((kv, str(e)))


def validate_keyvalue_ajax(request):
    kv_class = request.POST.get('kv_class', None)
    obj_pk = request.POST.get('obj_pk', None)
    key = request.POST.get('key', None)
    value = request.POST.get('value', None)
    key_pk = request.POST.get('key_pk', None)
    delete_key = request.POST.get('delete_key', None)
    print "{0} {1} {2} {3} {4}".format(kv_class, key, value, key_pk,
            delete_key)

    if not (kv_class and bool(delete_key)):
        return HttpResponse(
            json.dumps({'success': False, 'message': 'missing class'})
        )
    if not key:
        return HttpResponse(
            json.dumps({'success': False, 'message': 'Missing key'})
        )
    if not value:
        return HttpResponse(
            json.dumps({'success': False, 'message': 'Missing value'})
        )

    if delete_key == 'true':
        return HttpResponse(json.dumps({'success': True}))
    try:
        Klass, KVClass = resolve_class(kv_class)
        obj = Klass.objects.get(pk=obj_pk)
    except ObjectDoesNotExist:
        return HttpResponse(
            json.dumps(
                {'success': False, 'message': 'Missing valid class info'}
            )
        )

    if key_pk:
        try:
            kv = KVClass.objects.get(pk=key_pk)
        except KVClass.DoesNotExist:
            return HttpResponse(
                json.dumps({'success': False,
                            'message': "Can't find that Key Value pair."})
            )
    else:
        kv = KVClass(key=key, value=value, obj=obj)

    try:
        kv.clean()
    except ValidationError, e:
        return HttpResponse(
            json.dumps({'success': False, 'message': e.messages[0]})
        )

    return HttpResponse(json.dumps({'success': True}))

def resolve_class(kv_clas):
    return Network, Network.networkkeyvalue_set.related.model


def keyvalue(request):
    obj = Network.objects.all()[0]
    if request.method == 'POST':
        process_kv(request.POST.items(), obj.networkkeyvalue_set.related.model)
        pass
    attrs = obj.networkkeyvalue_set.all()
    aa_options = get_aa(obj.networkkeyvalue_set.model)
    return render(request, 'keyvalue/keyvalue.html', {
        'kv_class': 'network',
        'obj_pk': obj.pk,
        'attrs': attrs,
        'object': obj,
        'aa_options': aa_options,
        'existing_keyvalue': attrs,
    })
