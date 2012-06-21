from django import forms
from django.forms import ModelForm

from mozdns.nameserver.models import Nameserver


class NameserverForm(ModelForm):
    class Meta:
        model = Nameserver
        exclude = ('glue',)
        glue = forms.CharField(max_length=256,
            help_text="Enter Glue record if the NS server is within "
            "the domain you are assigning the NS server to.")


class NSDelegated(forms.Form):
    server = forms.CharField()
    server_ip_address = forms.CharField()
