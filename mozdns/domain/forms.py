from django.forms import ModelForm
from mozdns.domain.models import Domain


class DomainUpdateForm(ModelForm):
    class Meta:
        model = Domain
        fields = ('soa', 'delegated')


class DomainForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(DomainForm, self).__init__(*args, **kwargs)
        self.fields['soa'].choices = sorted(
            self.fields['soa'].choices,
            key=lambda s: '.'.join(reversed(s[1].split('.')))
        )

    class Meta:
        model = Domain
        fields = ('soa', 'name')
