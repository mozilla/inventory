from django import forms
from django.forms import widgets

from core.hwadapter.models import HWAdapter

from truth.models import Truth


class HWAdapterForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(HWAdapterForm, self).__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['dhcp_scope'] = forms.ChoiceField(
                choices=(
                    [('', '------------')] +
                    list(Truth.objects.all().values_list('name', 'name'))
                ),
                widget=forms.Select(attrs={'class': 'dhcp-scopes'}),
                required=False
            )

    class Meta:
        model = HWAdapter
        fields = (
            'name',
            'mac',
            'group',
            'description',
            'sreg',
        )
        widgets = {
            'sreg': widgets.HiddenInput
        }
