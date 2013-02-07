from django.shortcuts import render
from django.http import HttpResponse

from mozdns.utils import get_zones

from core.search.compiler.django_compile import compile_to_django
import simplejson as json
from gettext import gettext as _
from itertools import izip

from jinja2 import Environment, PackageLoader, ChoiceLoader
env = Environment(loader=ChoiceLoader(
    [PackageLoader('mozdns.record', 'templates'),
     PackageLoader('core.search', 'templates')]
))

MAX_NUM_OBJECTS = 5000


def request_to_search(request):
    search = request.GET.get("search", None)
    adv_search = request.GET.get("advanced_search", "")

    if adv_search:
        if search:
            search += " AND " + adv_search
        else:
            search = adv_search
    return search


def handle_shady_search(search):
    if not search:
        return HttpResponse("What do you want?!?")
    dos_terms = ["10", "com", "mozilla.com", "mozilla", "network:10/8",
                 "network:10.0.0.0/8"]
    if search in dos_terms:
        return HttpResponse("Denial of Service attack prevented. The search "
                            "term '{0}' is too general".format(search))
    return None


def search_ajax(request):
    template = env.get_template('search/core_search_results.html')

    def html_response(**kwargs):
        overflow_results = {}
        for type_, count in kwargs['meta']['counts'].items():
            if count > MAX_NUM_OBJECTS:
                overflow_results[type_] = count
                kwargs['objects'][type_] = kwargs['objects'][type_][:MAX_NUM_OBJECTS]
        kwargs['MAX_NUM_OBJECTS'] = MAX_NUM_OBJECTS
        kwargs['overflow_results'] = json.dumps(overflow_results)
        return template.render(**kwargs)
    return _search(request, html_response)


def search_dns_text(request):
    def render_rdtype(rdtype_set, **kwargs):
        response_str = ""
        for obj in rdtype_set:
            response_str += _("{0:<6}".format(obj.pk) +
                              obj.bind_render_record(**kwargs) + "\n")
        return response_str

    def text_response(**kwargs):
        response_str = ""
        # XXX make this a for loop you noob
        for type_ in ['SOA', 'NS', 'MX', 'SRV', 'CNAME', 'SSHFP', 'TXT',
                      'A', 'INTR', 'PTR']:
            response_str += render_rdtype(kwargs['objects'][type_])
        response_str += render_rdtype(kwargs['objects']['INTR'])
        response_str += render_rdtype(kwargs['objects']['INTR'], reverse=True)
        return json.dumps({'text_response': response_str})

    return _search(request, text_response)


def _search(request, response):
    search = request_to_search(request)

    errors = handle_shady_search(search)
    if errors:
        return errors

    obj_map, error_resp = compile_to_django(search)
    if not obj_map:
        return HttpResponse(json.dumps({'error_messages': error_resp}))
    obj_counts = {}
    total_objects = 0
    for type_, q in obj_map.iteritems():
        obj_counts[type_] = q.count() if q else 0
        total_objects += obj_counts[type_]
    results = {
        'meta': {
            'counts': obj_counts,
            'total_objects': total_objects,
            'search': search,
        },
        'objects': obj_map
    }
    return HttpResponse(response(**results))


def search(request):
    """Search page"""
    search = request.GET.get('search', '')
    return render(request, "search/core_search.html", {
        "search": search,
        "zones": sorted([z.name for z in get_zones()], reverse=True)
    })


def get_zones_json(request):
    return HttpResponse(json.dumps([z.name for z in get_zones()]))
