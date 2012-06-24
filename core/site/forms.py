from django import forms

from core.site.models import Site
from core.network.models import Network
class SiteForm(forms.ModelForm):
    name = forms.CharField()
    networks = forms.ModelMultipleChoiceField(
            queryset=Network.objects.all(),
            widget=forms.CheckboxSelectMultiple,
            required=False,
            )

    class Meta:
        model = Site

