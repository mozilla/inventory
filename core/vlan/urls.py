from django.conf.urls.defaults import patterns, url

from core.vlan.views import (VlanListView, VlanCreateView, vlan_detail,
                             update_vlan, VlanDeleteView)

urlpatterns = patterns('',
                       url(r'^$', VlanListView.as_view()),
                       url(r'^create/$', VlanCreateView.as_view()),
                       url(r'^(?P<vlan_pk>[\w-]+)/$', vlan_detail),
                       url(r'^(?P<vlan_pk>[\w-]+)/update/$', update_vlan),
                       url(r'^(?P<pk>[\w-]+)/delete/$',
                           VlanDeleteView.as_view()),
                       )
