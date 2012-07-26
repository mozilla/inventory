from django.forms import ModelForm

from mozdns.sshfp.models import SSHFP


class SSHFPForm(ModelForm):
    class Meta:
        model = SSHFP
        exclude = ('fqdn',)
