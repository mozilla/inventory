from django.forms import ModelForm
from mozdns.mx.models import MX

class MXForm( ModelForm ):
    class Meta:
        model   = MX
        exclude = ('fqdn',)
