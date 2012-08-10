from django import forms
from django.forms import ModelForm
from mozdns.cname.models import CNAME


class CNAMEForm(ModelForm):
    class Meta:
        model = CNAME
        exclude = ('data_domain', 'fqdn')
        fields = ('label', 'domain', 'data', 'views', 'ttl', 'comment')
        widgets = {'views': forms.CheckboxSelectMultiple}
        # https://code.djangoproject.com/ticket/9321
