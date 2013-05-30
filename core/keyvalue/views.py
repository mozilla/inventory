from django.shortcuts import render
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.http import HttpResponse
from django.http import Http404

from core.keyvalue.utils import get_aa, get_docstrings

import simplejson as json

from core.network.models import NetworkKeyValue
from core.range.models import RangeKeyValue
from core.site.models import SiteKeyValue
from mozdns.soa.models import SOAKeyValue
from core.registration.static.models import StaticRegKeyValue
from core.vlan.models import VlanKeyValue
from core.group.models import GroupKeyValue
from core.hwadapter.models import HWAdapterKeyValue

#from systems.models import KeyValue as SystemKeyValue

klasses = (
    NetworkKeyValue,
    RangeKeyValue,
    SiteKeyValue,
    SOAKeyValue,
    VlanKeyValue,
    #SystemKeyValue,
    StaticRegKeyValue,
    GroupKeyValue,
    HWAdapterKeyValue
)
kv_users = {}
for klass in klasses:
    kv_users[klass.__name__.lower()] = klass.obj.field.related.parent_model


def process_kv(kv, obj, KVClass):
    existing_kvs = []
    delete_kvs = []
    new_kvs = []
    for k, v in kv:
        if k.startswith('existing_delete_'):
            try:
                delete_kv = KVClass.objects.get(
                    pk=k.strip('existing_delete_v_')
                )
            except KVClass.DoesNotExist:
                continue  # It was deleted
            delete_kvs.append(delete_kv)
        elif k.startswith('existing_v_'):
            try:
                existing_kv = KVClass.objects.get(pk=k.strip('existing_v_'))
            except KVClass.DoesNotExist:
                continue  # It was deleted
            if existing_kv in delete_kvs:
                continue
            existing_kv.value = v
            existing_kvs.append(existing_kv)
        elif k.startswith('attr_new_key_'):
            k_num = k.strip('attr_new_key_')
            value_k_name = 'attr_new_value_' + k_num
            for ki, vi in kv:
                if ki == value_k_name:
                    new_kv = KVClass(key=v, value=vi, obj=obj)
                    new_kvs.append(new_kv)
    return_attrs = []
    for kv in existing_kvs + new_kvs:
        try:
            kv.clean()
            kv.save()
            return_attrs.append((kv, None))
        except ValidationError, e:
            return_attrs.append((kv, str(e)))
    for kv in delete_kvs:
        kv.delete()


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

    try:
        obj, Klass = resolve_obj(kv_class, obj_pk)
    except ObjectDoesNotExist:
        return HttpResponse(
            json.dumps(
                {'success': False, 'message': 'Missing valid class info'}
            )
        )

    if key_pk:
        try:
            kv = obj.keyvalue_set.get(pk=key_pk)
        except Klass.DoesNotExist:
            return HttpResponse(
                json.dumps(
                    {'success': False,
                     'message': "Can't find that Key Value pair."}
                )
            )

        if delete_key != 'true':
            kv.value = value
    else:
        kv = Klass(key=key, value=value, obj=obj)

    try:
        kv.validate_unique()
        kv.clean()
    except ValidationError, e:
        return HttpResponse(
            json.dumps({'success': False, 'message': e.messages[0]})
        )

    return HttpResponse(json.dumps({'success': True}))


def resolve_class(obj_class):
    if obj_class not in kv_users:
        raise Http404()
    return kv_users[obj_class]


def resolve_obj(obj_class, obj_pk):
    if obj_class not in kv_users:
        raise Http404("Can't find this kv object")
    if obj_class.lower() not in kv_users:
        raise Http404()
    Klass = kv_users[obj_class.lower()]
    try:
        obj = Klass.objects.get(pk=obj_pk)
    except Klass.DoesNotExist:
        raise Http404()
    return obj, obj.keyvalue_set.model


def keyvalue(request, obj_class, obj_pk):
    obj, KVKlass = resolve_obj(obj_class, obj_pk)
    if request.method == 'POST':
        process_kv(request.POST.items(), obj, KVKlass)
    attrs = obj.keyvalue_set.all()
    aa_options = get_aa(obj.keyvalue_set.model)
    docs = get_docstrings(KVKlass)
    return render(request, 'keyvalue/keyvalue.html', {
        'kv_class': obj_class,
        'obj_pk': obj.pk,
        'attrs': attrs,
        'object': obj,
        'aa_options': aa_options,
        'existing_keyvalue': attrs,
        'docs': docs,
    })
