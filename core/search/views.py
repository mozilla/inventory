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

from core.search.parser import parse
from core.search.search import compile_search

import pdb
import re
import ipaddr
import operator
import simplejson as json


from jinja2 import Environment, PackageLoader
env = Environment(loader=PackageLoader('core.search', 'templates'))

def search_ajax(request):
    pdb.set_trace()
    search = request.GET.get("search", None)
    if not search:
        return HttpResponse("What do you want?!?")
    dos_terms = ["10", "com", "mozilla.com", "mozilla",  "network:10/8",
            "network:10.0.0.0/8"]
    if search in dos_terms:
        return HttpResponse("Denial of Service attack prevented. The search "
                "term '{0}' is to general".format(search))
    query = parse(search)
    print "----------------------"
    print query
    print "----------------------"

    x = compile_search(query)
    addrs, cnames, domains, intrs, mxs, nss, ptrs, srvs, txts, misc = x
    template = env.get_template('search/core_search_results.html')
    return HttpResponse(template.render(
                                    **{
                                        "misc": misc,
                                        "search": search,
                                        "addrs": addrs,
                                        "cnames": cnames,
                                        "domains": domains,
                                        "intrs": intrs,
                                        "mxs": mxs,
                                        "nss": nss,
                                        "ptrs": ptrs,
                                        "srvs": srvs,
                                        "txts": txts
                                    }
                        ))
def search(request):
    """Search page"""
    search = request.GET.get('search','')
    return render(request, "search/core_search.html", {
        "search": search
    })
