from django import forms
from django.core.exceptions import ValidationError

from core.site.models import Site


class SiteForm(forms.ModelForm):
    name = forms.CharField()

    class Meta:
        model = Site
        exclude = ('full_name',)

    def validate_unique(self):
        try:
            self.instance.validate_unique()
        except ValidationError, e:
            if 'full_name' in e.message_dict:
                e.message_dict['__all__'] = e.message_dict['full_name']
            self._update_errors(e.message_dict)
