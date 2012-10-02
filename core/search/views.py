from django.db.models import Q
from django.shortcuts import render
from django.http import HttpResponse

import pdb
from core.search.compiler.compiler import Compiler

from jinja2 import Environment, PackageLoader
env = Environment(loader=PackageLoader('core.search', 'templates'))

def search_ajax(request):
    search = request.GET.get("search", None)
    if not search:
        return HttpResponse("What do you want?!?")
    dos_terms = ["10", "com", "mozilla.com", "mozilla",  "network:10/8",
            "network:10.0.0.0/8"]
    if search in dos_terms:
        return HttpResponse("Denial of Service attack prevented. The search "
                "term '{0}' is to general".format(search))

    #x = compile_search(query)
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
