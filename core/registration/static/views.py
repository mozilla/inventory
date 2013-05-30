from django.http import HttpResponse
from django.core.exceptions import ValidationError
from django.forms.formsets import formset_factory
from django.db import transaction, IntegrityError

from core.registration.static.forms import StaticRegAutoForm
from core.hwadapter.forms import HWAdapterForm
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
                hwform.instance.sreg = sreg  # WTF, why doesn't initial do this?
                try:
                    hw = hwform.save()
                    save_kv_pairs(
                        hw, hwform.data, 'kv-{0}-'.format(hwform.prefix)
                    )  # prefix thing is kind of hacky
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

    #if not result:
    if errors:
        return HttpResponse(json.dumps({
            'success': False,
            'errors': errors
        }))
    return HttpResponse(json.dumps({
        'success': True
    }))
