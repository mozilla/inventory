from django import forms

from core.range.models import Range


class RangeForm(forms.ModelForm):
    class Meta:
        model = Range
        exclude = (
            'start_upper', 'start_lower', 'end_upper', 'end_lower',
            'dhcpd_raw_include', 'rtype'
        )

    def __init__(self, *args, **kwargs):
        super(RangeForm, self).__init__(*args, **kwargs)
        self.fields['start_str'].label = "Start Address"
        self.fields['end_str'].label = "End Address"
        #self.fields['dhcpd_raw_include'].label = "DHCP Config Extras"
        #self.fields['dhcpd_raw_include'].widget.attrs.update(
        #    {'cols': '80', 'style': 'display: none;width: 680px'})
