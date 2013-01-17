from django import forms


class IpSearchForm(forms.Form):
    IP_TYPES = (
        ('4', 'IPv4'),
        ('6', 'IPv6'),
    )
    ip_type = forms.ChoiceField(label='Address Type',
                                choices=IP_TYPES)
    search_ip = forms.CharField(label='IP Address or IP Network')
