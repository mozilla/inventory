from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.shortcuts import get_object_or_404, redirect, render_to_response
from django.shortcuts import render
from django.contrib import messages
from django.forms.util import ErrorList
from django.http import HttpResponse

from systems.models import System

from core.interface.static_intr.models import StaticInterface
from core.interface.static_intr.models import StaticIntrKeyValue
from core.interface.static_intr.forms import StaticInterfaceForm
from core.interface.static_intr.forms import FullStaticInterfaceForm
from core.interface.static_intr.forms import StaticInterfaceQuickForm
from core.interface.static_intr.forms import CombineForm
from core.keyvalue.utils import get_attrs, update_attrs, get_aa, get_docstrings
from core.keyvalue.utils import get_docstrings, dict_to_kv
from core.views import CoreDeleteView, CoreCreateView
from core.range.models import Range
from core.network.utils import calc_parent_str

from mozdns.domain.models import Domain
from mozdns.address_record.models import AddressRecord
from mozdns.ptr.models import PTR

import pdb
import re
import ipaddr
import operator
import simplejson as json


def search_ajax(request):
    return HttpResponse(data)

def search(request):
    """Search page"""
    if request.method == "GET":
        return render(request, 'search/core_search.html', {})
    else:
        search = request.POST.get('search', None)
        while True:
            l
        if not search:
            return render(request, 'search/core_search.html', {})

