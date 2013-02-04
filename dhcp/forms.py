from django import forms
from django.forms.extras.widgets import SelectDateWidget

import models

class AddDHCPScopeForm(forms.Form):
    scope_name = forms.CharField(max_length=32, required=True, widget=forms.TextInput(attrs={'size':'48'}))
    scope_description = forms.CharField(max_length=32, required=True, widget=forms.TextInput(attrs={'size':'48'}))

class DHCPScopeOverrideForm(forms.ModelForm):
    dhcp_scope = forms.CharField(max_length=32, required=True, widget=forms.TextInput(attrs={'size':'48'}))
    #override_text = forms.CharField(max_length=32, required=True, widget=forms.Textarea(attrs={'rows':'60', 'cols':'80'}))
    class Meta:
        model = models.DHCPOverride
class EditDHCPScopeForm(forms.Form):
    SUBNET_CHOICES = (
            ('255.255.224.0', '255.255.224.0'),
            ('255.255.240.0', '255.255.240.0'),
            ('255.255.248.0', '255.255.248.0'),
            ('255.255.252.0', '255.255.252.0'),
            ('255.255.254.0', '255.255.254.0'),
            ('255.255.255.0', '255.255.255.0'),
            ('255.255.255.128', '255.255.255.128'),
            ('255.255.255.192', '255.255.255.192'),
            ('255.255.255.224', '255.255.255.224'),
            ('255.255.255.240', '255.255.255.240'),
            ('255.255.255.248', '255.255.255.248'),
            ('255.255.255.252', '255.255.255.252'),
            ('255.255.255.254', '255.255.255.254')
            )
    YES_NO_CHOICES = (
            (0, 'No'),
            (1, 'Yes'),
            )
    CHOICES = (
            ('True', 'True'),
            ('False', 'False'),
            )
 
    scope_name = forms.CharField(max_length=32,widget=forms.TextInput(attrs={'size':'48'}))
    domain_name = forms.CharField(max_length=64, required=False, widget=forms.TextInput(attrs={'size':'48'}))
    router = forms.CharField(max_length=64, required=False, widget=forms.TextInput(attrs={'size':'48'}))
    scope_start = forms.CharField(max_length=64, required=True, widget=forms.TextInput(attrs={'size':'48'}))
    scope_end = forms.CharField(max_length=64, required=True, widget=forms.TextInput(attrs={'size':'48'}))
    scope_netmask = forms.CharField(max_length=64, required=True, widget=forms.Select(choices=SUBNET_CHOICES))
    pool_start = forms.CharField(max_length=64, required=True, widget=forms.TextInput(attrs={'size':'48'}))
    pool_end = forms.CharField(max_length=64, required=True, widget=forms.TextInput(attrs={'size':'48'}))
    ntp_server1 = forms.CharField(max_length=64, required=False, widget=forms.TextInput(attrs={'size':'48'}))
    ntp_server2 = forms.CharField(max_length=64, required=False, widget=forms.TextInput(attrs={'size':'48'}))
    dns_server1 = forms.CharField(max_length=64, required=False, widget=forms.TextInput(attrs={'size':'48'}))
    dns_server2 = forms.CharField(max_length=64, required=False, widget=forms.TextInput(attrs={'size':'48'}))
    allow_booting = forms.CharField(max_length=64, required=False, widget=forms.Select(choices=CHOICES))
    allow_bootp = forms.CharField(max_length=64, required=False, widget=forms.Select(choices=CHOICES))
    class Meta:
        fields = [
                    "scope_name", 
                    "scope_start",
                    'scope_netmask',
                    'scope_notes',
                    'filename',
                    'pool_start',
                    'pool_end',
                    'pool_deny_dynamic_bootp_agents',
                    'allow_booting',
                    'allow_bootp',
                    'filename',
                    'option_subnet_mask',
                    'ntp_server1',
                    'ntp_server2', 
                    'dns_server1',
                    'dns_server2',
                    'router',
                    'domain_name',
                    'option_routers'
                ]
