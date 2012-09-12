from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from mozdns.master_form.views import *
from mozdns.api.v1.api import v1_dns_api


urlpatterns = patterns('',
    url(r'^ajax_form/', mozdns_record_form_ajax),
    url(r'^ajax_search/', mozdns_record_search_ajax),
    url(r'^$', mozdns_record),
)
