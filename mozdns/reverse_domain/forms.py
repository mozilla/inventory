from django.forms import ModelForm
from django import forms
from mozdns.reverse_domain.models import ReverseDomain
from mozdns.soa.models import SOA

class ReverseDomainUpdateForm( ModelForm ):
    class Meta:
        model   = ReverseDomain
        exclude = ('name','master_reverse_domain', 'ip_type')


class ReverseDomainForm( ModelForm ):
    choices = ( (1,'Yes'),
                (0,'No'),
              )
    inherit_soa = forms.ChoiceField(widget=forms.RadioSelect, choices=choices, required=False)
    class Meta:
        model   = ReverseDomain
        exclude = ('master_reverse_domain',)

class BootStrapForm( forms.Form ):
    name = forms.CharField(max_length=100)
    soa  = forms.ChoiceField( required=False )

    def __init__(self, *args, **kwargs):
        super(BootStrapForm, self).__init__(*args, **kwargs)
        # Update the form with recent data
        choices = [('','-----------' )]+[ (soa.pk,soa) for soa in SOA.objects.all() ]
        self['soa'].field._choices += choices
