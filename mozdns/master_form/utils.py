from mozdns.address_record.models import AddressRecord
from mozdns.address_record.forms import AddressRecordFQDNForm
from mozdns.address_record.forms import AddressRecordForm
from mozdns.ptr.models import PTR
from mozdns.ptr.forms import PTRForm
from mozdns.srv.models import SRV
from mozdns.srv.forms import SRVForm, FQDNSRVForm
from mozdns.txt.models import TXT
from mozdns.txt.forms import TXTForm, FQDNTXTForm
from mozdns.mx.models import MX
from mozdns.mx.forms import MXForm, FQDNMXForm
from mozdns.cname.models import CNAME
from mozdns.cname.forms import CNAMEFQDNForm, CNAMEForm
from mozdns.soa.models import SOA
from mozdns.soa.forms import SOAForm
from mozdns.domain.models import Domain

def get_klasses(record_type):
    """
    Given record type string, grab its class and forms.
    """
    return {
        'A': (AddressRecord, AddressRecordForm, AddressRecordFQDNForm),
        'CNAME': (CNAME, CNAMEForm, CNAMEFQDNForm),
        #'DOMAIN': (Domain, DomainForm, DomainForm),
        'MX': (MX, MXForm, FQDNMXForm),
        #'NS': (Nameserver, NameserverForm, NameserverForm),
        'PTR': (PTR, PTRForm, PTRForm),
        'SOA': (SOA, SOAForm, SOAForm),
        'SRV': (SRV, SRVForm, FQDNSRVForm),
        'TXT': (TXT, TXTForm, FQDNTXTForm),
    }.get(record_type, (None, None, None))
