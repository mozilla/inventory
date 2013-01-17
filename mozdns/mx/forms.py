from django import forms
from mozdns.mx.models import MX
from mozdns.forms import BaseForm


class MXForm(BaseForm):
    class Meta:
        model = MX
        exclude = ('fqdn',)
        widgets = {'views': forms.CheckboxSelectMultiple}


class FQDNMXForm(BaseForm):
    class Meta:
        model = MX
        exclude = ('label', 'domain')
        fields = ('fqdn', 'server', 'priority', 'ttl', 'views', 'description')
        widgets = {'views': forms.CheckboxSelectMultiple}
