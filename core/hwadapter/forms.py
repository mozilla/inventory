from django import forms
from django.forms import widgets

from core.hwadapter.models import HWAdapter

from truth.models import Truth


class HWAdapterForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(HWAdapterForm, self).__init__(*args, **kwargs)

        if not self.instance.pk:
            truths = Truth.objects.all().values_list('name', 'name')
            self.fields['dhcp_scope'] = forms.ChoiceField(
                choices=(
                    [('', '------------')] +
                    list(truths.order_by('-name'))
                ),
                widget=forms.Select(attrs={'class': 'dhcp-scopes'}),
                required=False
            )

    class Meta:
        model = HWAdapter
        fields = (
            'mac',
            'name',
            'description',
            'sreg',
            'enable_dhcp',
        )
        widgets = {
            'sreg': widgets.HiddenInput
        }

    def has_changed(self):
        if self.changed_data == ['dhcp_scope']:
            # This is automatically set by the UI sometimes. If this is the
            # only thing that has changed the user probably didn't want a
            # hardware adapter created
            return False
        return bool(self.has_changed)
