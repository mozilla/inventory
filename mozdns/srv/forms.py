from django import forms
from django.forms import ModelForm

from mozdns.srv.models import SRV
from mozdns.forms import BaseForm


class SRVForm(BaseForm):
    class Meta:
        model = SRV
        exclude = ('fqdn',)
        widgets = {'views': forms.CheckboxSelectMultiple}


class FQDNSRVForm(BaseForm):
    class Meta:
        model = SRV
        exclude = ('label', 'domain')
        widgets = {'views': forms.CheckboxSelectMultiple}

