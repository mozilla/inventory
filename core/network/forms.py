from django import forms
from django.db.models.query import EmptyQuerySet

from core.site.models import Site
from core.network.models import Network
from core.network.utils import calc_networks, calc_parent

import pdb

class NetworkForm(forms.ModelForm):
    sites = forms.ModelMultipleChoiceField(
            queryset=Site.objects.all(),
            widget=forms.CheckboxSelectMultiple,
            required=False
            )

    def __init__(self, *args, **kwargs):
        super(NetworkForm, self).__init__(*args, **kwargs)
        if self.instance.pk is None:
            self.fields['sites'].queryset = EmptyQuerySet()
            return
        parent = calc_parent(self.instance)
        if not parent:
            return

        self.fields['sites'].queryset = parent.sites.all()

    class Meta:
        model = Network
        exclude = ('ip_upper','ip_lower', 'prefixlen')


