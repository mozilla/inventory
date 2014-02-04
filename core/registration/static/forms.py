from django import forms
from django.forms import widgets

from core.registration.static.models import StaticReg
from core.utils import resolve_ip_type
from mozdns.forms import BaseForm
from mozdns.utils import ensure_label_domain


class StaticRegForm(BaseForm):
    class Meta:
        model = StaticReg
        fields = (
            'label', 'domain', 'ip_str', 'ip_type', 'ttl', 'views', 'system',
            'name', 'description', 'decommissioned'
        )
        widgets = {'views': forms.CheckboxSelectMultiple}


class StaticRegFQDNForm(BaseForm):
    class Meta:
        model = StaticReg
        fields = (
            'fqdn', 'ip_str', 'ip_type', 'ttl', 'views', 'name', 'description',
            'decommissioned'
        )
        widgets = {'views': forms.CheckboxSelectMultiple}


class StaticRegAutoForm(BaseForm):
    def clean(self, *args, **kwargs):
        self.instance.ip_type = resolve_ip_type(self.cleaned_data['ip_str'])[0]
        self.instance.label, self.instance.domain = ensure_label_domain(
            self.cleaned_data['fqdn']
        )
        return super(StaticRegAutoForm, self).clean(*args, **kwargs)

    class Meta:
        model = StaticReg
        fields = (
            'fqdn', 'ip_str', 'views', 'description', 'system', 'ttl', 'name',
            'decommissioned'
        )
        widgets = {
            'views': forms.CheckboxSelectMultiple,
            'system': widgets.HiddenInput
        }
