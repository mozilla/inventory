from django.forms import ModelForm

from mozdns.sshfp.models import SSHFP
from mozdns.forms import BaseForm


class SSHFPForm(BaseForm):
    class Meta:
        model = SSHFP
        exclude = ('fqdn',)


class FQDNSSHFPForm(BaseForm):
    class Meta:
        model = SSHFP
        include = ('fqdn', 'key', 'algorithm_number', 'fingerprint_type',
                   'views', 'description')
        exclude = ('label', 'domain')
