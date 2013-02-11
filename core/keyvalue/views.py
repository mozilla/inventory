from django.shortcuts import render
from core.network.models import Network
from core.keyvalue.utils import get_aa

from django import forms
#from django.forms.formsets import formset_factory


class KVForm(forms.Form):
    key = forms.CharField()
    value = forms.CharField()
    check = forms.BooleanField(
        required=True, label="Mark for deletion"
    )


def keyvalue(request):
    print request.POST
    obj = Network.objects.all()[0]
    attrs = obj.networkkeyvalue_set.all()
    aa_options = get_aa(obj.networkkeyvalue_set.model)
    return render(request, 'keyvalue/keyvalue.html', {
        'forms': [KVForm()],
        'object': obj,
        'aa_options': aa_options,
        'existing_keyvalue': attrs,
    })
