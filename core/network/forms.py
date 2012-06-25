from django import forms
from django.db.models.query import EmptyQuerySet

from core.site.models import Site
from core.network.models import Network
from core.network.utils import calc_networks, calc_parent

import pdb

class NetworkForm(forms.ModelForm):
    site = forms.ModelChoiceField(
            queryset=Site.objects.all(),
            empty_label="(Defaults to parent's site.)",
            required=False
            )

    def __init__(self, *args, **kwargs):
        super(NetworkForm, self).__init__(*args, **kwargs)


    class Meta:
        model = Network
        exclude = ('ip_upper','ip_lower', 'prefixlen')


