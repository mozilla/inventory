from django.conf.urls.defaults import patterns, url

from core.range.views import *  # noqa

urlpatterns = patterns(
    '',
    url(r'^$', RangeListView.as_view()),
    url(r'^find_range/', redirect_to_range_from_ip),
    url(r'^ajax_find_related/', ajax_find_related, name='ajax-find-related'),
    url(r'find_related/', find_related, name='find-related'),
    url(r'range_usage_ajax/$', range_usage_ajax),
    url(r'create/', RangeCreateView.as_view(), name='create-range'),
    url(r'(?P<pk>[\w-]+)/update/$', RangeUpdateView.as_view()),
    url(r'(?P<pk>[\w-]+)/delete/$', RangeDeleteView.as_view()),
    url(r'^get_next_available_ip_by_range/(?P<range_id>\d+)[/]$',
        get_next_available_ip_by_range, name='system-adapter-next-ip'),
    url(r'^usage_text/$', range_usage_text),
    url(r'^debug_show_ranges/$', debug_show_ranges),
    url(r'(?P<range_pk>[\w-]+)/$', range_detail),
)
