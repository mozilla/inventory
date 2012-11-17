from django.conf.urls.defaults import *
from reversion_compare.views import history_view, compare_view
from mozdns.api.v1.api import v1_dns_api


urlpatterns = patterns('',
    url(r'history_view/(?P<object_class>[\w-]+)/history/compare/', compare_view),
    url(r'history_view/(?P<object_class>[\w-]+)/(?P<object_id>[\w-]+)/', history_view),
)
