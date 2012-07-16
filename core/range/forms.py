from django import forms
from django.db.models.query import EmptyQuerySet

from core.range.models import Range

import pdb


class RangeForm(forms.ModelForm):
    class Meta:
        model = Range
        exclude = ('start', 'end')

    def __init__(self, *args, **kwargs):
        super(RangeForm, self).__init__(*args, **kwargs)
        self.fields['dhcpd_raw_include'].label = "DHCP Config Extras"
        self.fields['dhcpd_raw_include'].widget.attrs.update({'cols': '80',
            'style': 'display: none;width: 680px'})
