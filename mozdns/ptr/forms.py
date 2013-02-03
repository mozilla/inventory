from django import forms
from mozdns.ptr.models import PTR
from mozdns.forms import BaseForm


class PTRForm(BaseForm):
    def delete_instance(self, instance):
        instance.delete()

    class Meta:
        model = PTR
        exclude = ('ip', 'reverse_domain', 'ip_upper',
                   'ip_lower')
        include = ('name', 'ip_str', 'ip_type', 'ttl', 'views', 'description')

        widgets = {'views': forms.CheckboxSelectMultiple}
