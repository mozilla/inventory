from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from mozdns.zone_creation.views import zone_creation


urlpatterns = patterns('',
    url(r'^$', zone_creation),
)
