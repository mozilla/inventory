from django.forms import ModelForm

from mozdns.view.models import View


class ViewForm(ModelForm):
    class Meta:
        model = View
