from django import forms
from django.forms.extras.widgets import SelectDateWidget

from models import UnmanagedSystem, Owner, UserLicense

from datetime import datetime, timedelta

class CSVForm(forms.Form):
    csv = forms.FileField()

class UserSystemForm(forms.ModelForm):

    date_purchased = forms.DateField(widget=SelectDateWidget(years=range(1999,datetime.today().year + 2)), initial=datetime.now())

    class Meta:
        model = UnmanagedSystem
        fields = ('owner',
                  'serial',
                  'asset_tag',
                  'date_purchased',
                  'cost',
                  'operating_system',
                  'server_model',
                  'notes')


class OwnerForm(forms.ModelForm):

    class Meta:
        model = Owner
        fields = ['name', 'user_location', 'email', 'note']

class UserLicenseForm(forms.ModelForm):

    class Meta:
        model = UserLicense
        fields = ['username', 'version', 'license_type', 'license_key', 'owner']
