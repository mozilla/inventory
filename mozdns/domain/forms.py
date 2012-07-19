from django.forms import ModelForm
from django import forms
from mozdns.domain.models import Domain


class DomainUpdateForm(ModelForm):
    class Meta:
        model = Domain
        exclude = ('name', 'master_domain',)


class DomainForm(ModelForm):
    class Meta:
        model = Domain
        exclude = ('master_domain','is_reverse', 'dirty')
