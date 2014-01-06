from django import forms

from mozdns.forms import BaseForm
from mozdns.nameserver.models import Nameserver
from mozdns.address_record.models import AddressRecord
from core.registration.static.models import StaticReg


class NameserverForm(BaseForm):
    class Meta:
        model = Nameserver
        exclude = ('addr_glue', 'sreg_glue')
        fields = ('domain', 'server', 'ttl', 'description', 'views')
        widgets = {'views': forms.CheckboxSelectMultiple}

    def __init__(self, *args, **kwargs):
        super(NameserverForm, self).__init__(*args, **kwargs)
        self.fields['domain'].choices = sorted(
            self.fields['domain'].choices, key=lambda d: d[1]
        )
        if not self.instance:
            return
        if not self.instance.glue:
            # If it doesn't have glue, it doesn't need it.
            return
        addr_glue = AddressRecord.objects.filter(
            label=self.instance.glue.label,
            domain=self.instance.glue.domain)
        sreg_glue = StaticReg.objects.filter(
            label=self.instance.glue.label,
            domain=self.instance.glue.domain)

        glue_choices = []
        for glue in addr_glue:
            glue_choices.append(("addr_{0}".format(glue.pk), str(glue)))
        for glue in sreg_glue:
            glue_choices.append(("sreg_{0}".format(glue.pk), str(glue)))

        if isinstance(self.instance.glue, AddressRecord):
            initial = "addr_{0}".format(self.instance.glue.pk)
        elif isinstance(self.instance.glue, StaticReg):
            initial = "sreg_{0}".format(self.instance.glue.pk)

        self.fields['glue'] = forms.ChoiceField(choices=glue_choices,
                                                initial=initial)


class NSDelegated(forms.Form):
    server = forms.CharField()
    server_ip_address = forms.CharField()
