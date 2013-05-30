from django.conf.urls.defaults import patterns, url

from core.hwadapter.views import (
    ajax_hw_adapter_create, HWAdapterUpdateView, ajax_hw_adapter_delete
)

urlpatterns = patterns('',
    url(r'^create[/]$', ajax_hw_adapter_create),
    url(r'^(?P<pk>\d+)/update[/]$', HWAdapterUpdateView.as_view()),
    url(r'^(?P<pk>\d+)/delete[/]$', ajax_hw_adapter_delete)
)
