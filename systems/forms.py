from django import forms
from django.forms.extras.widgets import SelectDateWidget
try:
    from functools import wraps
except ImportError:
    from django.utils.functional import wraps  # Python 2.3, 2.4 fallback.

import models
from datetime import datetime

from systems.constants import VALID_SYSTEM_SUFFIXES
from core.site.models import Site

import re



def has_changed(instance, field):
    old_value = instance.__class__._default_manager.\
            filter(pk=instance.pk).values(field).get()[field]
    return not getattr(instance, field) == old_value

class SystemRackForm(forms.ModelForm):
    class Meta:
        model = models.SystemRack
        exclude = ('location',)

class ServerModelForm(forms.ModelForm):
    class Meta:
        model = models.ServerModel

class AllocationForm(forms.ModelForm):
    class Meta:
        model = models.Allocation

class RackFilterForm(forms.Form):

    site = forms.ChoiceField(
        required=False,
        choices=[('', 'ALL')] + [
            (m.id, m) for m in Site.objects.all()
        ])
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'ALL')] +
            [(m.id, m) for m in models.SystemStatus.objects.all()]
    )
    rack = forms.ChoiceField(
        required=False,
        choices=[('', 'ALL')] + [
            (m.id, '{0} - {1}'.format(m.site.full_name, m.name) if m.site else '' + ' ' +  m.name)
            for m in models.SystemRack.objects.all().order_by('site', 'name')
        ]
    )

    allocation = forms.ChoiceField(
        required=False,
        choices=[('', 'ALL')] + [(m.id, m)
                    for m in models.Allocation.objects.all()])

    show_decommissioned = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super(RackFilterForm, self).__init__(*args, **kwargs)
        self.fields['site'].choices = [('', 'ALL')] + [(m.id, m.full_name) for m in Site.objects.all()]
        self.fields['status'].choices = [('', 'ALL')] + [(m.id, m) for m in models.SystemStatus.objects.all()]
        self.fields['rack'].choices = [('', 'ALL')] + [
            (m.id, '{0} - {1}'.format(m.site.full_name, m.name) if m.site else '' + ' ' +  m.name)
            for m in models.SystemRack.objects.all().order_by('site', 'name')
        ]
        self.fields['allocation'].choices = [('', 'ALL')] + [(m.id, m) for m in models.Allocation.objects.all()]
        self.fields['show_decommissioned'].initial = False

def return_data_if_true(f):
    @wraps(f)
    def wrapper(self, *args, **kwargs):
        field_name = f.__name__.split("_", 1)[1]
        data = self.cleaned_data[field_name]
        if data:
            return data
        return f(self, *args, **kwargs)
    return wrapper


class SystemForm(forms.ModelForm):
    rack_order = forms.DecimalField(
        required=False,
        widget=forms.TextInput(attrs={'size': '3'})
    )

    purchase_date = forms.DateField(
        required=False,
        widget=SelectDateWidget(years=range(1999, datetime.today().year + 2)),
        initial=datetime.now()
    )

    change_password = forms.DateField(
        required=False,
        widget=SelectDateWidget
    )

    warranty_start = forms.DateField(
        required=False,
        widget=SelectDateWidget(years=range(1999, datetime.today().year + 5)),
    )

    warranty_end = forms.DateField(
        required=False,
        widget=SelectDateWidget(years=range(1999, datetime.today().year + 50)),
    )

    class Meta:
        model = models.System
        fields = ('hostname',
                  'serial',
                  'switch_ports',
                  'patch_panel_port',
                  'oob_ip',
                  'oob_switch_port',
                  'system_status',
                  'system_rack',
                  'system_type',
                  'rack_order',
                  'is_dhcp_server',
                  'is_dns_server',
                  'is_nagios_server',
                  'is_puppet_server',
                  'is_switch',
                  'change_password',
                  'operating_system',
                  'server_model',
                  'allocation',
                  'asset_tag',
                  'purchase_date',
                  'purchase_price',
                  'warranty_start',
                  'warranty_end',
                  'licenses',
                  'notes',
                  )

    def __init__(self, *args, **kwargs):
        super(SystemForm, self).__init__(*args, **kwargs)
        self.fields['hostname'].widget.attrs['style'] = 'width: 400px;'

    def clean_hostname(self):
        """
            We're now starting to enforce fqdn for inventory hostnames. The following
            will check if we're editing or inserting. If inserting enforce fqdn
            ending in mozilla.(com|net|org) otherwise leave it be.
            Later on we can enforce fqdn by removing the self.instance.pk negate below
        """
        data = self.cleaned_data['hostname']
        if self.instance.pk:
            return data
        for suffix in VALID_SYSTEM_SUFFIXES:
            if data.endswith(suffix):
                return data
        raise forms.ValidationError(
            'Hostname must end in ' + ', '.join(VALID_SYSTEM_SUFFIXES)
        )

    @return_data_if_true
    def clean_operating_system(self):
        name = self.data.get('js_os_name')
        version = self.data.get('js_os_version')
        if name is not None and version is not None:
            os, c = models.OperatingSystem.objects.get_or_create(
                name=name,
                version=version)
            return os

        return None

    @return_data_if_true
    def clean_server_model(self):
        vendor = self.data.get('js_server_model_vendor')
        model = self.data.get('js_server_model_model')
        if vendor is not None and model is not None:
            server_model, c = models.ServerModel.objects.get_or_create(
                vendor=vendor,
                model=model)
            return server_model

        return None

    @return_data_if_true
    def clean_allocation(self):
        name = self.data.get('js_allocation_name')

        if name is not None:
            allocation, c = models.Allocation.objects.get_or_create(
                name=name,
            )
            return allocation

        return None

    @return_data_if_true
    def clean_system_status(self):
        name_status = self.data.get('js_status_name')
        color_status = self.data.get('js_status_color')
        code_color_status = self.data.get('js_status_code')
        if name_status is not None and code_color_status is not None and color_status is not None:
            status_model, c = models.SystemStatus.objects.get_or_create(
                status=name_status,
                color=color_status,
                color_code=code_color_status,
            )
            return status_model
        return None


class RackSystemForm(forms.ModelForm):

    rack_order = forms.DecimalField(
        required=False,
        widget=forms.TextInput(attrs={'size': '3'}))

    class Meta:
        model = models.System
        fields = ('rack_order',
                  'hostname',
                  'asset_tag',
                  'server_model',
                  'allocation',
                  'oob_ip',)


class CSVImportForm(forms.Form):
    csv = forms.FileField()
