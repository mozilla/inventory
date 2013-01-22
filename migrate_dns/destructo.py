from mozdns.address_record.models import AddressRecord
from mozdns.cname.models import CNAME
from mozdns.domain.models import Domain
from mozdns.mx.models import MX
from mozdns.nameserver.models import Nameserver
from mozdns.ptr.models import PTR
from mozdns.soa.models import SOA
from mozdns.srv.models import SRV
from mozdns.txt.models import TXT
from reversion.models import Version, Revision



def destroy():
    Version.objects.all().delete()
    Revision.objects.all().delete()
    TXT.objects.all().delete()
    SRV.objects.all().delete()
    CNAME.objects.all().delete()
    Nameserver.objects.all().delete()
    PTR.objects.all().delete()
    MX.objects.all().delete()
    AddressRecord.objects.all().delete()
    SOA.objects.all().delete()
    Domain.objects.all().delete()
