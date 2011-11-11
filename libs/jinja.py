from settings import env
from django.http import HttpResponse
from django.template.context import Context
from jinja2 import FileSystemLoader, Environment
import settings
from settings import TEMPLATE_DIRS as template_dirs
import jinja2
def render_to_string(filename, context={}):
    template = env.get_template(filename)
    rendered = template.render(**context)
    return rendered
 
default_mimetype = 'text/html'
def jinja_render_to_response(filename, context={}, request=None, mimetype=default_mimetype):
    if request:
        context['request'] = request
        context['user'] = request.user
    rendered = render_to_string(filename, context)
    return HttpResponse(rendered,mimetype=mimetype)

class DjangoTemplate(jinja2.Template):
    def render(self, *args, **kwargs):
        if args and isinstance(args[0], Context):
            for d in reversed(args[0].dicts):
                kwargs.update(d)
            args = []
        return super(DjangoTemplate, self).render(*args, **kwargs)

class DjangoEnvironment(jinja2.Environment):
    template_class = DjangoTemplate

jenv = DjangoEnvironment(loader=FileSystemLoader(template_dirs))
jenv.filters['url'] = settings.jinja_url
