from django.conf.urls.defaults import patterns, url
from django.views.decorators.csrf import csrf_exempt

from core.range.views import (RangeListView, RangeCreateView, RangeDeleteView,
        redirect_to_range_from_ip, update_range, delete_range_attr,
        get_next_available_ip_by_range, get_all_ranges_ajax, range_usage_text,
        range_detail)

urlpatterns = patterns('',
       url(r'^$', csrf_exempt(RangeListView.as_view())),
       url(r'find_range/',
           csrf_exempt(redirect_to_range_from_ip)),
       url(r'create/$', csrf_exempt(
           RangeCreateView.as_view())),
       url(r'(?P<range_pk>[\w-]+)/update/$',
           csrf_exempt(update_range)),
       url(r'attr/(?P<attr_pk>[\w-]+)/delete/$',
           csrf_exempt(delete_range_attr)),
       url(r'(?P<pk>[\w-]+)/delete/$',
           csrf_exempt(RangeDeleteView.as_view())),
       url(r'^get_next_available_ip_by_range/(?P<range_id>\d+)[/]$',
           csrf_exempt(get_next_available_ip_by_range),
           name='system-adapter-next-ip'),
       url(r'^get_all_ranges_ajax[/]', get_all_ranges_ajax,
           name='get-all-ranges-ajax'),
       url(r'^usage_text/$', csrf_exempt(range_usage_text)),
       url(r'(?P<range_pk>[\w-]+)/$',
           csrf_exempt(range_detail)),
       )
