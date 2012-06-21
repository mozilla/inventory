from django.forms import ModelForm
from django import forms
from mozdns.domain.models import Domain

class DomainUpdateForm( ModelForm ):
    class Meta:
        model   = Domain
        exclude = ('name','master_domain',)

class DomainForm( ModelForm ):
    choices = ( (1,'Yes'),
                (0,'No'),
              )
    inherit_soa = forms.ChoiceField(widget=forms.RadioSelect, choices=choices)
    class Meta:
        model   = Domain
        exclude = ('master_domain',)

