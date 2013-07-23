from django import forms
from django.core.exceptions import ValidationError

from core.site.models import Site
from core.vlan.models import Vlan
from core.network.models import Network


class NetworkForm(forms.ModelForm):
    site = forms.ModelChoiceField(
        queryset=Site.objects.all(),
        empty_label="(Defaults to parent's site.)",
        required=False)

    def __init__(self, *args, **kwargs):
        super(NetworkForm, self).__init__(*args, **kwargs)
        self.fields['dhcpd_raw_include'].label = "DHCP Config Extras"
        self.fields['dhcpd_raw_include'].widget.attrs.update(
            {'cols': '80', 'style': 'display: none;width: 680px'})

    class Meta:
        model = Network
        exclude = ('ip_upper', 'ip_lower', 'prefixlen')

    def validate_unique(self):
        try:
            self.instance.validate_unique()
        except ValidationError, e:
            self._update_errors(e.message_dict)


class NetworkForm_network(forms.Form):
    network = forms.CharField(required=True)
    IP_TYPE_CHOICES = (('4', 'ipv4'), ('6', 'ipv6'))
    ip_type = forms.ChoiceField(choices=IP_TYPE_CHOICES)


class NetworkForm_site(forms.Form):
    site = forms.ModelChoiceField(
        queryset=Site.objects.all(),
        required=True
    )


class NetworkForm_vlan(forms.Form):
    vlan = forms.ModelChoiceField(
        queryset=Vlan.objects.all(),
        required=True
    )

    CREATE_CHOICE = (
        ("existing", "Use existing VLAN template."),
        ("new", "Create New Vlan"),
        ("none", "Don't assign a vlan"),
    )

    create_choice = forms.ChoiceField(widget=forms.RadioSelect, initial='e',
                                      choices=CREATE_CHOICE)

    name = forms.CharField()
    number = forms.IntegerField()
