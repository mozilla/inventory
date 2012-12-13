from django.conf.urls.defaults import *
from django.views.decorators.csrf import csrf_exempt

from mozdns.create_zone.views import *

urlpatterns = patterns('',
    url(r'^$', create_zone, name='create-zone'),
    url(r'create_zone_ajax/$', create_zone_ajax, name='create-zone-ajax'),
)
