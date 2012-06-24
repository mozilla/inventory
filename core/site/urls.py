from django.conf.urls.defaults import *

from core.site.views import *

urlpatterns = patterns('',
    url(r'(?P<site_pk>[\w-]+)/update/$', update_site),
    url(r'(?P<site_pk>[\w-]+)/$', site_detail),
    url(r'create/$', SiteCreateView.as_view()),
    url(r'$', SiteListView.as_view()),
    url(r'(?P<pk>[\w-]+)/delete/$', SiteDeleteView.as_view()),

)
