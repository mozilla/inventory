from settings import env
from django.http import HttpResponse
def render_to_string(filename, context={}):
    template = env.get_template(filename)
    rendered = template.render(**context)
    return rendered
 
default_mimetype = 'text/html'
def render_to_response(filename, context={}, request=None, mimetype=default_mimetype):
    if request:
        context['request'] = request
    try:
        context['user'] = request.user
    except:
        pass
    rendered = render_to_string(filename, context)
    return HttpResponse(rendered,mimetype=mimetype)
def jinja_render_to_response(filename, context={}, request=None, mimetype=default_mimetype):
    if request:
        context['request'] = request
        context['user'] = request.user
    rendered = render_to_string(filename, context)
    return HttpResponse(rendered,mimetype=mimetype)
