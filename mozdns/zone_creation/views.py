from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.models import Q
from django.http import QueryDict
from django.forms.util import ErrorList, ErrorDict
from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.http import Http404

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
from mozdns.view.models import View
from mozdns.utils import ensure_label_domain
from mozdns.utils import prune_tree
import operator

from gettext import gettext as _, ngettext
import simplejson as json
import pdb


def zone_creation(request):
    return render(request, 'zone_creation/zone_creation.html', {})
