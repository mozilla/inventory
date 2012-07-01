from django import forms
from django.forms import ModelForm

from mozdns.nameserver.models import Nameserver
from mozdns.address_record.models import AddressRecord
from core.interface.static_intr.models import StaticInterface
import itertools

import pdb

class NameserverForm(ModelForm):
    class Meta:
        model = Nameserver
        exclude = ('addr_glue','intr_glue')
        widgets = {'views': forms.CheckboxSelectMultiple}

    def __init__(self, *args, **kwargs):
        super(NameserverForm, self).__init__(*args, **kwargs)
        if not self.instance:
            return
        if not self.instance.glue:
            # If it doesn't have glue, it doesn't need it.
            return
        addr_glue = AddressRecord.objects.filter(label=self.instance.glue.label,
                domain=self.instance.glue.domain)
        intr_glue = StaticInterface.objects.filter(label=self.instance.glue.label,
                domain=self.instance.glue.domain)

        glue_choices = []
        for glue in addr_glue:
            glue_choices.append(("addr_{0}".format(glue.pk),str(glue)))
        for glue in intr_glue:
            glue_choices.append(("intr_{0}".format(glue.pk),str(glue)))

        if isinstance(self.instance.glue, AddressRecord):
            initial = "addr_{0}".format(self.instance.glue.pk)
        elif isinstance(self.instance.glue, StaticInterface):
            initial = "intr_{0}".format(self.instance.glue.pk)

        self.fields['glue'] = forms.ChoiceField(choices=glue_choices,
                initial=initial)




class NSDelegated(forms.Form):
    server = forms.CharField()
    server_ip_address = forms.CharField()
