from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from mozdns.master_form.views import mozdns_record
from mozdns.api.v1.api import v1_dns_api


urlpatterns = patterns('',
    url(r'^$', mozdns_record, name='mozdns-index'),
    url(r'^record/', include('mozdns.master_form.urls')),
    url(r'^address_record/', include('mozdns.address_record.urls')),
    url(r'^cname/', include('mozdns.cname.urls')),
    url(r'^domain/', include('mozdns.domain.urls')),
    url(r'^mx/', include('mozdns.mx.urls')),
    url(r'^nameserver/', include('mozdns.nameserver.urls')),
    url(r'^ptr/', include('mozdns.ptr.urls')),
    url(r'^soa/', include('mozdns.soa.urls')),
    url(r'^srv/', include('mozdns.srv.urls')),
    url(r'^txt/', include('mozdns.txt.urls')),
    url(r'^sshfp/', include('mozdns.sshfp.urls')),
    url(r'^view/', include('mozdns.view.urls')),
    url(r'^bind/', include('mozdns.mozbind.urls')),
    url(r'^api/', include(v1_dns_api.urls)),

)
