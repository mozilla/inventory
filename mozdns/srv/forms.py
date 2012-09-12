from mozdns.srv.models import SRV
from django.forms import ModelForm


class SRVForm(ModelForm):
    class Meta:
        model = SRV
        exclude = ('fqdn',)


class FQDNSRVForm(ModelForm):
    class Meta:
        model = SRV
        exclude = ('label', 'domain')
