from django import forms
from django.forms.extras.widgets import SelectDateWidget
try:
    from functools import wraps
except ImportError:
    from django.utils.functional import wraps  # Python 2.3, 2.4 fallback.

import models
from datetime import datetime, timedelta


class RackFilterForm(forms.Form):

    location = forms.ChoiceField(
        required=False,
        choices=[('', 'All')] + [(m.id, m)
                    for m in models.Location.objects.all()])
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'All')] + [(m.id, m)
                    for m in models.SystemStatus.objects.all()])
    rack = forms.ChoiceField(
        required=False,
        choices=[('', 'All')] + [(m.id, m.location.name + ' ' +  m.name)
                    for m in models.SystemRack.objects.all()])
    allocation = forms.ChoiceField(
        required=False,
        choices=[('', 'All')] + [(m.id, m)
                    for m in models.Allocation.objects.all()])


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
        widget=forms.TextInput(attrs={'size': '3'}))
    purchase_date = forms.DateField(
            required=False,
            widget=SelectDateWidget(years=range(1999,datetime.today().year + 2)), 
            initial=datetime.now()
            )
    change_password = forms.DateField(
        required=False,
        widget=SelectDateWidget)
    #notes = forms.CharField(
    #    required=False,
    #    widget = forms.widgets.Textarea(attrs={'style': 'width: 922px; height: 240px;'})
    #)
    #licenses = forms.CharField(
    #    required=False,
    #    widget = forms.widgets.Textarea(attrs={'style': 'width: 922px; height: 240px;'})
    #)

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
    def clean_status_system(self):
	name_status = self.data.get('js_status_name')
	color_status = self.data.get('js_status_color')
	code_color_status = self.data.get('js_status_code')
	if name_status is not None and code_status is not None:
		status_model, c= models.SystemStatus.objects.get_or_create(
			status=name_status,
		        status_color = color_status,	
			status_code= code_color_status,
					
		)
		return status_model
	
	return None


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
                  'rack_order',
                  'asset_tag',
                  'is_dhcp_server',
                  'is_dns_server',
                  'is_nagios_server',
                  'is_puppet_server',
                  'is_switch',
                  'purchase_date',
                  'change_password',
                  'purchase_price',
                  'operating_system',
                  'server_model',
                  'allocation',
                  'licenses',
                  'notes',
                  )


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
