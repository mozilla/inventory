from django import forms
from django.forms.extras.widgets import SelectDateWidget

from models import UnmanagedSystem, Owner, UserLicense
try:
    from functools import wraps
except ImportError:
    from django.utils.functional import wraps  # Python 2.3, 2.4 fallback.

from datetime import datetime, timedelta


def return_data_if_true(f):
	@wraps(f)
	def wrapper(self, *args, **kwargs):
		field_name = f.__name__.split("_", 1)[1]
		data = self.cleaned_data[field_name]
        	if data:
			return data
		return f(self, *args, **kwargs)
	return wrapper



class CSVForm(forms.Form):
    csv = forms.FileField()

class UserSystemForm(forms.ModelForm):

    date_purchased = forms.DateField(widget=SelectDateWidget(years=range(1999,datetime.today().year + 2)), initial=datetime.now())
    loaner_return_date = forms.DateField(widget=SelectDateWidget(), initial=datetime.now(), required=False)

    class Meta:
        model = UnmanagedSystem
        fields = ('owner',
                  'serial',
                  'asset_tag',
                  'date_purchased',
                  'cost',
                  'is_loaned',
                  'is_loaner',
                  'bug_number',
                  'loaner_return_date',
                  'operating_system',
                  'server_model',
                  'notes')


class OwnerForm(forms.ModelForm):

    class Meta:
        model = Owner
        fields = ['name', 'user_location', 'email', 'note']

class UserLicenseForm(forms.ModelForm):
    @return_data_if_true
    def clean_owner(self):
        name = self.data.get('js_owner_name')
        #user_location = self.data.get('js_owner_user_location')
        email = self.data.get('js_owner_email')
        note = self.data.get('js_owner_note')
        if name is not none:
            owner, c = owner.objects.get_or_create(
                    name = name,
                    #user_location=user_location,
                    email = email,
                    note = note)
            return owner
    class Meta:
        model = UserLicense
        fields = ['username', 'version', 'license_type', 'license_key', 'owner', 'user_operating_system']
