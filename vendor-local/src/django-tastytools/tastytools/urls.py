from django.conf.urls.defaults import patterns, include, url
from views import doc, howto

urlpatterns = patterns('',
    (r'^doc', doc),
    (r'^howto', howto),
)
