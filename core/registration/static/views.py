from django.http import HttpResponse
from django.core.exceptions import ValidationError
from django.shortcuts import render, get_object_or_404
from django.forms.formsets import formset_factory
from django.db import transaction, IntegrityError

from core.registration.static.forms import StaticRegAutoForm
from core.hwadapter.forms import HWAdapterForm
from core.hwadapter.models import HWAdapterKeyValue
from core.search.compiler.django_compile import search_type
from core.registration.static.combine_utils import (
    generate_sreg_bundles, combine_multiple, combine, generate_possible_names
)

from systems.models import System

import MySQLdb
import simplejson as json


def save_kv_pairs(obj, qd, prefix):
    """
    Look for keyvalue pairs in a query dict that match a certain prefix and
    save them to obj's keyvalue store. This function doesn't catch exceptions.
    """
    def parse_kv(field, value):
        if field.startswith(prefix):
            return field.replace(prefix, ''), value
        return None, None

    def save_kv(key, value):
        obj.keyvalue_set.model.objects.create(key=key, value=value, obj=obj)

    for field, value in qd.iteritems():
        key, value = parse_kv(field, value)
        if key and value:
            save_kv(key, value)


def ajax_create_sreg(request):
    HWAdapterFormset = formset_factory(HWAdapterForm)

    sreg_form = StaticRegAutoForm(request.POST, prefix='sreg')
    hw_formset = HWAdapterFormset(request.POST, prefix='hwadapters')

    @transaction.commit_on_success
    def save_objects():
        # This really is a pile of hack
        errors = {}
        try:
            if not sreg_form.is_valid():
                errors['sreg'] = sreg_form.errors.items()
                return errors
            sreg = sreg_form.save()
            save_kv_pairs(
                sreg, sreg_form.data, 'kv-{0}-'.format(sreg_form.prefix)
            )  # prefix thing is kind of hacky
        except ValidationError, e:
            errors['sreg'] = [('__all__', e.messages)]
            return errors

        error_list = []  # Where to keep the errors
        error = False  # Flag if there were errors
        for hwform in filter(lambda f: f.has_changed(), hw_formset):
            hwform.initial['sreg'] = sreg
            if hwform.is_valid():
                hwform.instance.sreg = sreg  # why doesn't initial do this?
                try:
                    hw = hwform.save()
                    save_kv_pairs(
                        hw, hwform.data, 'kv-{0}-'.format(hwform.prefix)
                    )  # prefix thing is kind of hacky
                    dhcp_scope = hwform.cleaned_data.get('dhcp_scope', None)
                    if dhcp_scope:
                        HWAdapterKeyValue.objects.get_or_create(
                            obj=hw, key='dhcp_scope', value=dhcp_scope
                        )
                except IntegrityError, e:
                    # the MySQL driver is such a load of crap
                    if 'Duplicate entry' in str(e):
                        error_list.append(
                            [('', 'This seems to be a duplicate entry')]
                        )
                    error = True
                else:
                    error_list.append([])
            else:
                error = True
                error_list.append(hwform.errors.items())

        if error:
            transaction.rollback()
            errors['hw_adapters'] = error_list

        return errors

    errors = save_objects()

    if errors:
        return HttpResponse(json.dumps({
            'success': False,
            'errors': errors
        }))
    return HttpResponse(json.dumps({
        'success': True
    }))


def combine_status_list(request):
    qd = request.POST or request.GET
    if qd:
        search = qd.get('search', '')
        start = qd.get('start', '0')
        end = qd.get('end', '100')
        records, error = search_type(search, 'SYS')
        if not search or error or not (start.isdigit() and end.isdigit()):
            records = []
        else:
            try:
                records = records[int(start):int(end)]
            except MySQLdb.OperationalError, e:
                if "Got error " in str(e) and " from regexp" in str(e):
                    # This is nasty. If the user is using an invalid regex
                    # patter, the db might shit a brick
                    records = []
                else:
                    raise

        bundles = []
        for system in records:
            for name in generate_possible_names(system.hostname):
                bundles += generate_sreg_bundles(system, name)

        combine_multiple(bundles, rollback=True)

        return render(request, 'static_reg/combine_status_list.html', {
            'bundles': bundles,
            'search': search
        })
    else:
        return render(request, 'static_reg/combine_status_list.html', {
            'search': ''
        })


def ajax_combine_sreg(request):
    if not request.POST:
        return HttpResponse(json.dumps({
            'success': False,
            'errors': 'Missing object pks'
        }))

    a_pk = request.POST.get('a_pk', None)
    ptr_pk = request.POST.get('ptr_pk', None)
    system_pk = request.POST.get('system_pk', None)
    name = request.POST.get('name', None)

    if not (a_pk and ptr_pk and system_pk and name):
        return HttpResponse(json.dumps({
            'success': False,
            'errors': 'Missing object pks'
        }))

    a_pk, ptr_pk, system_pk = int(a_pk), int(ptr_pk), int(system_pk)

    system = get_object_or_404(System, pk=system_pk)

    bundles = generate_sreg_bundles(system, name)

    bundle = None
    for a_bundle in bundles:
        if (a_bundle['a'].pk == a_pk and a_bundle['ptr'].pk == ptr_pk and
                a_bundle['system'].pk == system_pk and
                a_bundle['fqdn'] == name):
            bundle = a_bundle
            break

    assert bundle is not None

    combine(bundle)
    return HttpResponse(json.dumps({
        'success': not bundle['errors'],
        'redirect_url': system.get_absolute_url(),
        'errors': bundle.get('errors', '')
    }))
