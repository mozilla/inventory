from django import forms
from django.forms import ModelForm
from mozdns.cname.models import CNAME


class CNAMEForm(ModelForm):
    class Meta:
        model = CNAME
        exclude = ('target_domain', 'fqdn')
        fields = ('label', 'domain', 'target', 'views', 'ttl', 'comment')
        widgets = {'views': forms.CheckboxSelectMultiple}
        # https://code.djangoproject.com/ticket/9321

class CNAMEFQDNForm(ModelForm):
    class Meta:
        model = CNAME
        fields = ('fqdn', 'target', 'views', 'ttl', 'comment')
        widgets = {'views': forms.CheckboxSelectMultiple}
        # https://code.djangoproject.com/ticket/9321
