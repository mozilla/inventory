from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.urlresolvers import reverse


def doc(request, api_name):
    view_data = {
        'api_url': reverse('api_%s_top_level' % api_name, args=[api_name])
    }
    return render_to_response('tastytools/doc.html', view_data,
            context_instance=RequestContext(request))


def howto(request, api_name):
    return render_to_response('tastytools/howto.html', {'api_name': api_name},
            context_instance=RequestContext(request))
