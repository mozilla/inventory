from django.forms import ModelForm
from mozdns.address_record.models import AddressRecord

class AddressRecordForm( ModelForm ):
    class Meta:
        model   = AddressRecord
        exclude = ('ip_upper','ip_lower', 'reverse_domain', 'fqdn')
