from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin
from django.views.generic.simple import direct_to_template
from django.views import static

from middleware.restrict_to_remote import allow_anyone

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
admin.autodiscover()


urlpatterns = patterns('',
    # Example:


    # Uncomment the admin/doc line below and add 'django.contrib.admindocs'
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
    url(r'^$', 'systems.views.home', name='system-home'),
    url(r'^en-US/$', 'systems.views.home', name='system-home'),
    url(r'^misc/$', direct_to_template, {'template': 'misc.html'}, name='misc-list'),
    (r'^a(\d+)/$', 'systems.views.system_show_by_asset_tag'),
    (r'^systems/', include('systems.urls')),
    (r'^en-US/systems/', include('systems.urls')),
    (r'^oncall/', include('oncall.urls')),
    (r'^reports/', include('reports.urls')),
    (r'^dhcp/', include('dhcp.urls')),
    (r'^truth/', include('truth.urls')),
    (r'^user_systems/', include('user_systems.urls')),
    (r'^build/', include('build.urls')),
    (r'^tasty/', include('api_v3.urls')),
    (r'^en-US/tasty/', include('api_v3.urls')),
    (r'^api/', include('api_v1.urls')),
    (r'^api/v1/', include('api_v1.urls')),
    (r'^api/v2/', include('api_v2.urls')),
    (r'^tokenapi/', include('api_v2.urls')),

    (r'^en-US/mozdns/', include('mozdns.urls')),
    (r'^mozdns/', include('mozdns.urls')),
    (r'^reversion_compare/', include('reversion_compare.urls')),
    (r'^en-US/core/', include('core.urls')),
    (r'^core/', include('core.urls')),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', allow_anyone(static.serve),
            {'document_root': settings.STATIC_DOC_ROOT}),
    )
