from django.forms import ModelForm
from mozdns.cname.models import CNAME

class CNAMEForm( ModelForm ):
    class Meta:
        model   = CNAME
        exclude = ('data_domain', 'fqdn')
