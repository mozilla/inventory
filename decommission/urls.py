from django.conf.urls.defaults import patterns, url
from decommission.views import decommission

urlpatterns = patterns(
    '',
    url(r'^hosts[/]', decommission, name='decommission'),
)
