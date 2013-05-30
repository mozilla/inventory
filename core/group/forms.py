from django import forms

from core.group.models import Group


class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
