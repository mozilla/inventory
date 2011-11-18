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
    try:
        context['user'] = request.user
    except:
        pass
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
from django.template.loader import BaseLoader
from django.template.loaders.app_directories import app_template_dirs
from django.template import TemplateDoesNotExist
from django.core import urlresolvers
from django.conf import settings
import jinja2

class Template(jinja2.Template):
    def render(self, context):
        # flatten the Django Context into a single dictionary.
        context_dict = {}
        for d in context.dicts:
            context_dict.update(d)
        return super(Template, self).render(context_dict)

class Loader(BaseLoader):
    is_usable = True

    env = jinja2.Environment(loader=jinja2.FileSystemLoader(app_template_dirs))
    env.template_class = Template

    # These are available to all templates.
    env.globals['url_for'] = urlresolvers.reverse
    env.globals['MEDIA_URL'] = settings.MEDIA_URL
    #env.globals['STATIC_URL'] = settings.STATIC_URL

    def load_template(self, template_name, template_dirs=None):
        try:
            template = self.env.get_template(template_name)
        except jinja2.TemplateNotFound:
            raise TemplateDoesNotExist(template_name)
        return template, template.filename

