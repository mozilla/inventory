from django import forms
from django.contrib.auth.models import User
from django.forms.widgets import HiddenInput

from oncall.models import OncallTimestamp, OncallAssignment
from oncall.constants import ONCALL_TYPES


def make_choices(oncall_type):
    oncall_users = User.objects.filter(**{oncall_type: 1})
    return [(u, u.get_profile().irc_nick) for u in oncall_users]


class OncallForm(forms.Form):
    class Meta:
        model = User

    def __init__(self, *args, **kwargs):
        super(OncallForm, self).__init__(*args, **kwargs)
        mtime = OncallTimestamp.objects
        for onc_type in ONCALL_TYPES:
            try:
                cur = OncallAssignment.objects.get(oncall_type=onc_type)
                cur_onc_name = cur.user.username
            except OncallAssignment.DoesNotExist:
                cur_onc_name = ''

            # dynamically add fields for each oncall type
            self.fields[onc_type] = forms.ChoiceField(
                label=onc_type.title() + ' Oncall',
                choices=make_choices(
                    'userprofile__is_{0}_oncall'.format(onc_type)
                ),
                initial=cur_onc_name
            )

            self.fields[onc_type + '_timestamp'] = forms.DateTimeField(
                widget=HiddenInput(),
                initial=mtime.get_or_create(oncall_type=onc_type)[0].updated_on
            )

    def save(self, *args, **kwargs):
        # Loop though oncall types and save the selected use as the new oncall
        # user.
        changes = []
        for onc_type in ONCALL_TYPES:
            new_oncall = User.objects.get(username=self.cleaned_data[onc_type])
            try:
                onc = OncallAssignment.objects.get(oncall_type=onc_type)
                if new_oncall != onc.user:
                    changes.append(
                        (onc_type, onc.user.username, new_oncall.username)
                    )
                onc.user = new_oncall
                onc.save()
            except OncallAssignment.DoesNotExist:
                OncallAssignment.objects.create(
                    oncall_type=onc_type,
                    user=new_oncall
                )
        return changes

    def clean(self):
        cleaned_data = super(OncallForm, self).clean()

        # Check for collisions
        for onc in ONCALL_TYPES:
            db_mtime = OncallTimestamp.objects.get(oncall_type=onc).updated_on
            if (cleaned_data.get(onc + '_timestamp', False) and
                    db_mtime != cleaned_data[onc + '_timestamp']):
                raise forms.ValidationError(
                    'Midair Collision on setting Oncall, please refresh.'
                )

        return cleaned_data
