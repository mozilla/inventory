from mozdns.soa.models import SOA
from mozdns.forms import BaseForm


class SOAForm(BaseForm):
    class Meta:
        model = SOA
