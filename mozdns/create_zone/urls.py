from django.conf.urls.defaults import patterns, url

from mozdns.create_zone.views import create_zone, create_zone_ajax

urlpatterns = patterns('',
                       url(r'^$', create_zone, name='create-zone'),
                       url(r'create_zone_ajax/$',
                           create_zone_ajax, name='create-zone-ajax'),
                       )
