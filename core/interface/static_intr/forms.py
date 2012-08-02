from django import forms
from django.forms import models
from django.core.exceptions import ValidationError

from core.interface.static_intr.models import StaticInterface
from mozdns.domain.models import Domain
from mozdns.view.models import View
from core.range.models import Range
from mozdns.validation import validate_label
from core.vlan.models import Vlan
from core.site.models import Site
from systems.models import System
from core.validation import validate_mac

import ipaddr
import pdb


def validate_ip(ip):
    try:
        ipaddr.IPv4Address(ip)
    except ipaddr.AddressValueError, e:
        try:
            ipaddr.IPv6Address(ip)
        except ipaddr.AddressValueError, e:
            raise ValidationError("IP address not in valid form.")


class CombineForm(forms.Form):
    mac = forms.CharField(validators=[validate_mac])
    system = forms.ModelChoiceField(queryset=System.objects.all())


class StaticInterfaceForm(forms.ModelForm):
    views = forms.ModelMultipleChoiceField(queryset=View.objects.all(),
            widget=forms.widgets.CheckboxSelectMultiple, required=False)
    label = forms.CharField(max_length=128, required=True)

    class Meta:
        model = StaticInterface
        exclude = ('ip_upper', 'ip_lower', 'reverse_domain',
                'system', 'fqdn')


class FullStaticInterfaceForm(forms.ModelForm):
    views = forms.ModelMultipleChoiceField(queryset=View.objects.all(),
            widget=forms.widgets.CheckboxSelectMultiple, required=False)

    class Meta:
        model = StaticInterface
        exclude = ('ip_upper', 'ip_lower', 'reverse_domain',
                'fqdn')


class StaticInterfaceQuickForm(forms.Form):
    mac = forms.CharField(validators=[validate_mac])
    label = forms.CharField(validators=[validate_label])
    ranges = Range.objects.all().select_related(depth=4).filter(
            network__vlan__id__isnull=False)
    ranges = sorted(ranges, cmp=lambda a, b: 1 if
            str(a.network.site.get_full_name()) >
            str(b.network.site.get_full_name()) else -1)
    range_choices = []
    for r in ranges:
        range_choices.append((str(r.pk), r.display()))

    range = forms.ChoiceField(choices=range_choices)
    """
    range = forms.ModelChoiceField(queryset=Range.objects.filter(
        network__vlan__id__isnull=False).select_related(depth=3))
    # TODO, can this be optimized?
    """
    views = forms.ModelMultipleChoiceField(queryset=View.objects.all(),
            widget=forms.widgets.CheckboxSelectMultiple, required=False)
