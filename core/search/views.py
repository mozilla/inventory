from django.db.models import Q
from django.shortcuts import render
from django.http import HttpResponse

from mozdns.api.v1.api import v1_dns_api

import pdb
from core.search.compiler.compiler import Compiler
import simplejson as json

from jinja2 import Environment, PackageLoader
env = Environment(loader=PackageLoader('core.search', 'templates'))

def resource_for_request(resource_name, filters, request):
    resource = v1_dns_api.canonical_resource_for(resource_name)
    objects = resource.get_object_list(request).filter(filters)
    return [resource.model_to_data(model, request) for model in objects]

def search_json(request):
    """This view just returns the raw JSON objects instead of rendering the
    objects with the HTML"""
    search = request.GET.get("search", None)
    if not search:
        return HttpResponse("{}")
    t = Compiler(search)
    x = t.compile_json()
    #addrs, cnames, domains, intrs, mxs, nss, ptrs, srvs, txts, misc = x
    addrf, cnamef, domainf, mxf, nsf, ptrf, srvf, sshfpf, intrf, txtf, misc = x
    meta = {
        # If the user wants object counts, let them use wc.
        'objects': {
            "misc": misc,
            "search": search,
            "addrs": resource_for_request('addressrecord', addrf, request)  if addrf else [],
            "cnames": resource_for_request('cname', cnamef, request) if cnamef else [],
            "domains": [],  # Not sure if this will ever have a resource
            "mxs": resource_for_request('mx', mxf, request) if mxf else [],
            "nss": resource_for_request('nameserver', nsf, request) if nsf else [],
            "ptrs": resource_for_request('ptr', ptrf, request) if ptrf else [],
            "srvs": resource_for_request('srv', srvf, request) if srvf else [],
            "sshfps": resource_for_request('sshfp', sshfpf, request) if srvf else [],
            "intrs": resource_for_request('staticinterface', intrf, request) if intrf else [],
            "txts": resource_for_request('txt', txtf, request) if txtf else [],
            "meta": [],  # TODO, write a resource for meta objects
            "search": search
        },
        }
    return HttpResponse(json.dumps(meta))


def search_ajax(request):
    search = request.GET.get("search", None)
    if not search:
        return HttpResponse("What do you want?!?")
    dos_terms = ["10", "com", "mozilla.com", "mozilla",  "network:10/8",
            "network:10.0.0.0/8"]
    if search in dos_terms:
        return HttpResponse("Denial of Service attack prevented. The search "
                "term '{0}' is to general".format(search))

    t = Compiler(search)
    x = t.compile_search()
    #addrs, cnames, domains, intrs, mxs, nss, ptrs, srvs, txts, misc = x
    addrs, cnames, domains, mxs, nss, ptrs, srvs, sshfps, intrs, txts, misc = x
    meta = {
            'counts':{
                'addr': addrs.count() if addrs else 0,
                'cname': cnames.count() if cnames else 0,
                'domain': domains.count() if domains else 0,
                'intr': intrs.count() if intrs else 0,
                'mx': mxs.count() if mxs else 0,
                'ns': nss.count() if nss else 0,
                'ptr': ptrs.count() if ptrs else 0,
                'txt': txts.count() if txts else 0,
                }
            }
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
                                        "txts": txts,
                                        "meta": meta,
                                        "search": search
                                    }
                        ))
def search(request):
    """Search page"""
    search = request.GET.get('search','')
    return render(request, "search/core_search.html", {
        "search": search
    })
