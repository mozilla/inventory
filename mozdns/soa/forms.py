from django.forms import ModelForm
from mozdns.soa.models import SOA


class SOAForm(ModelForm):
    class Meta:
        model = SOA
        exclude = ('serial', 'dirty',)
