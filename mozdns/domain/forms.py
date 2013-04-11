from django.forms import ModelForm
from mozdns.domain.models import Domain


class DomainUpdateForm(ModelForm):
    class Meta:
        model = Domain
        fields = ('soa', 'delegated')


class DomainForm(ModelForm):
    class Meta:
        model = Domain
        fields = ('soa', 'name', 'delegated')
