from django import forms
from django.forms import ModelForm


class BaseForm(ModelForm):
    comment = forms.CharField(widget=forms.HiddenInput, required=False)
