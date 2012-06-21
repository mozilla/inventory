from django.forms import ModelForm

from mozdns.txt.models import TXT

class TXTForm( ModelForm ):
    class Meta:
        model   = TXT
        exclude = ('fqdn',)
