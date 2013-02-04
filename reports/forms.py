from django import forms
from django.forms.extras.widgets import SelectDateWidget
try:
    from functools import wraps
except ImportError:
    from django.utils.functional import wraps  # Python 2.3, 2.4 fallback.

import models
from django.forms.widgets import RadioSelect, CheckboxSelectMultiple
from systems.models import Location, Allocation, SystemStatus, OperatingSystem
class MultiSelectFormField(forms.MultipleChoiceField):
    widget = forms.CheckboxSelectMultiple
    
    def __init__(self, *args, **kwargs):
        self.max_choices = kwargs.pop('max_choices', 0)
        super(MultiSelectFormField, self).__init__(*args, **kwargs)

    def clean(self, value):
        if not value and self.required:
            raise forms.ValidationError(self.error_messages['required'])
        if value and self.max_choices and len(value) > self.max_choices:
            raise forms.ValidationError('You must select a maximum of %s choice%s.'
                    % (apnumber(self.max_choices), pluralize(self.max_choices)))
        return value
class ReportForm(forms.Form):

    system_type = MultiSelectFormField(
        required=True,
        choices=[
                ('SYSTEM', 'SYSTEM'),
                #('UNMANAGED', 'UNMANAGED'),
            ] )
    output = forms.ChoiceField(
        required=False,
        choices=[
                ('SCREEN', 'SCREEN'),
                ('CSV', 'CSV'),
            ] )

    system_status = forms.MultipleChoiceField(
        required=False,
        
        widget=CheckboxSelectMultiple(attrs={'class': 'system_status'}),
        choices=[('-1', 'All')] + [(m.id, m) for m in SystemStatus.objects.all()])

    location = forms.MultipleChoiceField(
        required=False,
        widget=CheckboxSelectMultiple(attrs={'class': 'system_location'}),
        choices=[('-1', 'All')] + [(m.id, m) for m in Location.objects.all()])
                    
    allocation = forms.ChoiceField(
        required=False,
        choices=[('', 'All')] + [(m.id, m)
                    for m in Allocation.objects.all()])

    operating_system = forms.CharField(
            max_length=72,
            required = False
            )

    server_models = forms.CharField(
            max_length=72,
            required = False
            )
