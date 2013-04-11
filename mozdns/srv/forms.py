from django import forms

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
        fields = (
            'fqdn', 'target', 'port', 'priority', 'weight', 'ttl',
            'description', 'views'
        )
        exclude = ('label', 'domain')
        widgets = {'views': forms.CheckboxSelectMultiple}
