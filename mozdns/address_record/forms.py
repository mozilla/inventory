from django.forms import ModelForm
from django import forms
from mozdns.forms import BaseForm
from mozdns.address_record.models import AddressRecord


class AddressRecordForm(BaseForm):
    class Meta:
        model = AddressRecord
        exclude = ('ip_upper', 'ip_lower', 'reverse_domain', 'fqdn')
        fields = ('label', 'domain', 'ip_type', 'ip_str', 'views', 'ttl',
                'description')
        widgets = {'views': forms.CheckboxSelectMultiple}

class AddressRecordFQDNForm(BaseForm):
    class Meta:
        model = AddressRecord
        fields = ('fqdn', 'ip_type', 'ip_str', 'views', 'ttl', 'description')
        widgets = {'views': forms.CheckboxSelectMultiple}
