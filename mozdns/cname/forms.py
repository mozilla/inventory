from django import forms
from mozdns.cname.models import CNAME
from mozdns.forms import BaseForm


class CNAMEForm(BaseForm):
    class Meta:
        model = CNAME
        exclude = ('fqdn',)
        fields = ('label', 'domain', 'target', 'views', 'ttl', 'description')
        widgets = {'views': forms.CheckboxSelectMultiple}
        # https://code.djangoproject.com/ticket/9321


class CNAMEFQDNForm(BaseForm):
    class Meta:
        model = CNAME
        fields = ('fqdn', 'target', 'ttl', 'views', 'description')
        widgets = {'views': forms.CheckboxSelectMultiple}
        # https://code.djangoproject.com/ticket/9321
