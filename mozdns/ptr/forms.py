from django import forms
from django.forms import ModelForm
from mozdns.ptr.models import PTR


class PTRForm(ModelForm):
    class Meta:
        model = PTR
        exclude = ('ip', 'reverse_domain', 'ip_upper',
                'ip_lower')
        widgets = {'views': forms.CheckboxSelectMultiple}
