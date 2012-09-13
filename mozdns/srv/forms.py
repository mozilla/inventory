from django import forms
from django.forms import ModelForm

from mozdns.srv.models import SRV


class SRVForm(ModelForm):
    class Meta:
        model = SRV
        exclude = ('fqdn',)
        widgets = {'views': forms.CheckboxSelectMultiple}


class FQDNSRVForm(ModelForm):
    class Meta:
        model = SRV
        exclude = ('label', 'domain')
        widgets = {'views': forms.CheckboxSelectMultiple}

