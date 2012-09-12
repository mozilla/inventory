from django import forms
from django.forms import ModelForm
from mozdns.mx.models import MX


class MXForm(ModelForm):
    class Meta:
        model = MX
        exclude = ('fqdn',)
        widgets = {'views': forms.CheckboxSelectMultiple}

class FQDNMXForm(MXForm):
    class Meta:
        model = MX
        exclude = ('label', 'domain')
        widgets = {'views': forms.CheckboxSelectMultiple}
