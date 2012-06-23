from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template

from core.interface.static_reg.views import *

urlpatterns = patterns('',
    url(r'^$', direct_to_template, {'template': 'mozdns.html'}),

    url(r'build/$', sample_build),

    url(r'address_record/', include('mozdns.address_record.urls')),
    url(r'cname/', include('mozdns.cname.urls')),
    url(r'domain/', include('mozdns.domain.urls')),
    url(r'mx/', include('mozdns.mx.urls')),
    url(r'nameserver/', include('mozdns.nameserver.nameserver.urls')),
    url(r'ptr/', include('mozdns.ptr.urls')),
    url(r'soa/', include('mozdns.soa.urls')),
    url(r'srv/', include('mozdns.srv.urls')),
    url(r'txt/', include('mozdns.txt.urls')),

)

