from django import forms

from mozdns.forms import BaseForm
from mozdns.txt.models import TXT


class TXTForm(BaseForm):
    class Meta:
        model = TXT
        exclude = ('fqdn',)
        widgets = {'views': forms.CheckboxSelectMultiple}


class FQDNTXTForm(BaseForm):
    class Meta:
        model = TXT
        include = ('fqdn', 'txt_data', 'description', 'views')
        exclude = ('label', 'domain')
        widgets = {'views': forms.CheckboxSelectMultiple}
