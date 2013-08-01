from django.conf.urls.defaults import patterns, url

from mozdns.delete_zone.views import delete_zone, delete_zone_ajax

urlpatterns = patterns(
    '',
    url(r'^$', delete_zone, name='delete-zone'),
    url(r'delete_zone_ajax/$', delete_zone_ajax, name='delete-zone-ajax'),
)
