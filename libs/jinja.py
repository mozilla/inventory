from django.http import HttpResponse, HttpResponseRedirect
from settings.local import env
def jinja_render_to_response(filename, context={},mimetype='text/html'):
    template = env.get_template(filename)
    rendered = template.render(**context)
    return HttpResponse(rendered,mimetype=mimetype)
