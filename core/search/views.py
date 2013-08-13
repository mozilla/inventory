import MySQLdb

from django.shortcuts import render
from django.http import HttpResponse, Http404

from mozdns.utils import get_zones

from core.search.compiler.django_compile import compile_to_django
from core.search.compiler.django_compile import search_type

import simplejson as json
from gettext import gettext as _

from MySQLdb import OperationalError
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
    error_template = env.get_template('search/core_search_error.html')

    def html_response(**kwargs):
        if 'error_messages' in kwargs:
            return error_template.render(**kwargs)
        overflow_results = {}
        for type_, count in kwargs['meta']['counts'].items():
            if count > MAX_NUM_OBJECTS:
                overflow_results[type_] = count
                new_objs = kwargs['objects'][type_][:MAX_NUM_OBJECTS]
                kwargs['objects'][type_] = new_objs
        kwargs['MAX_NUM_OBJECTS'] = MAX_NUM_OBJECTS
        kwargs['overflow_results'] = json.dumps(overflow_results)
        return template.render(**kwargs)
    return _search(request, html_response)


def search_dns_text(request):
    def render_rdtype(rdtype_set, **kwargs):
        response_str = ""
        for obj in rdtype_set:
            response_str += _("{0:<6}".format(obj.pk) +
                              obj.bind_render_record(show_ttl=True, **kwargs) +
                              "\n")
        return response_str

    def text_response(**kwargs):
        if 'error_messages' in kwargs:
            return json.dumps({'text_response': kwargs['error_messages']})
        response_str = ""
        for type_ in ['NET', 'SITE', 'VLAN']:
            response_str += render_rdtype(kwargs['objects'][type_])
        for type_ in [
                'SOA', 'NS', 'MX', 'SRV', 'CNAME', 'SSHFP', 'TXT', 'A', 'SREG',
                'PTR', 'NET', 'SITE', 'VLAN', 'SYS', 'SREG']:
            response_str += render_rdtype(kwargs['objects'][type_])
        response_str += render_rdtype(kwargs['objects']['SREG'], reverse=True)
        return json.dumps({'text_response': response_str})

    return _search(request, text_response)


def _search(request, response):
    search = request_to_search(request)

    errors = handle_shady_search(search)
    if errors:
        return errors

    obj_map, error_resp = compile_to_django(search)
    if not obj_map:
        return HttpResponse(response(**{'error_messages': error_resp}))
    obj_counts = {}
    total_objects = 0
    try:  # We might have to catch shitty regular expressions
        for type_, q in obj_map.iteritems():
            obj_counts[type_] = q.count() if q else 0
            total_objects += obj_counts[type_]
    except OperationalError as why:
        return HttpResponse(response(**{'error_messages': str(why)}))

    format = request.GET.get('format', '')
    results = {
        'format': format,
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


def ajax_type_search(request):
    query = request.GET.get('query', '')
    record_type = request.GET.get('record_type', '')
    if not record_type:
        raise Http404
    records, error = search_type(query, record_type)
    if not query:
        return HttpResponse(json.dumps({record_type: []}))
    if error:
        records = []
    else:
        try:
            records = records[:50]
        except MySQLdb.OperationalError, e:
            if "Got error " in str(e) and " from regexp" in str(e):
                # This is nasty. If the user is using an invalid regex patter,
                # the db might shit a brick
                records = []
            else:
                raise
    return HttpResponse(json.dumps({
        record_type: [{'label': str(r), 'pk': r.pk} for r in records]
    }))


def get_zones_json(request):
    return HttpResponse(json.dumps([z.name for z in get_zones()]))
