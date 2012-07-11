from django import forms
from django.db.models.query import EmptyQuerySet

from core.range.models import Range

import pdb

class RangeForm(forms.ModelForm):
    class Meta:
        model = Range
        exclude = ('start','end')

