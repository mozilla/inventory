from django import forms

from mozdns.sshfp.models import SSHFP
from mozdns.forms import BaseForm


class SSHFPForm(BaseForm):
    class Meta:
        model = SSHFP
        exclude = ('fqdn',)
        widgets = {'views': forms.CheckboxSelectMultiple}


class FQDNSSHFPForm(BaseForm):
    class Meta:
        model = SSHFP
        include = ('fqdn', 'key', 'algorithm_number', 'fingerprint_type',
                   'views', 'description')
        exclude = ('label', 'domain')
        widgets = {'views': forms.CheckboxSelectMultiple}
