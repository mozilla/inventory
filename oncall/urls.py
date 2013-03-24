from django.conf.urls.defaults import patterns, url
from oncall.views import getoncall, oncall

urlpatterns = patterns(
    'oncall',
    url(r'^$', oncall, name='oncall'),
    url(r'getoncall[/](?P<oncall_type>.*)[/]$', getoncall, name='getoncall'),
)
