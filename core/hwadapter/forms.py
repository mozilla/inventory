from django import forms
from django.forms import widgets

from core.hwadapter.models import HWAdapter


class HWAdapterForm(forms.ModelForm):
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
