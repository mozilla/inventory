from django import forms

from core.site.models import Site
from core.network.models import Network
class NetworkForm(forms.ModelForm):
    sites = forms.ModelMultipleChoiceField(
            queryset=Site.objects.all(),
            widget=forms.CheckboxSelectMultiple
            )

    class Meta:
        model = Network
        exclude = ('ip_upper','ip_lower', 'prefixlen')


