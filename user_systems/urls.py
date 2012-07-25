from django.conf.urls.defaults import *
from django.conf import settings
from django.views.generic.list_detail import object_detail, object_list

from misc.generic_views import create_object, update_object, delete_object
import models
import forms

from datetime import datetime, timedelta

info_dict_by_asset_tag = {
    'queryset': models.UnmanagedSystem.objects.filter(id=6).select_related(
                    'owner', 'server_model', 'operating_system'
                ).order_by('owner__name'),
    'template_object_name': 'user_system'
}



owner_upgrade_info_dict = {
    'queryset': models.Owner.objects.filter(
        unmanagedsystem__date_purchased__lt=datetime.now() - timedelta(days=730)
        ).distinct(),
    'template_object_name': 'owner',
    'template_name': 'user_systems/owner_upgradeable_list.html'
}




urlpatterns = patterns('user_systems',
    url(r'^quicksearch/$', 'views.user_system_quicksearch_ajax', name='user-system-quicksearch'),
    url(r'^new/$', 'views.user_system_new', name="user-system-new"),
    url(r'^edit/(\d+)/$', 'views.user_system_edit', name="user-system-edit"),
    #url(r'^$', object_list, info_dict, name="user-system-list"),
    url(r'^$', 'views.user_system_index',  name="user-system-list"),
    url(r'^model/(?P<object_id>\d+)[/]$', 'views.show_by_model', name="user-system-list-by-model"),
    url(r'^show/a(\d+)/$', 'views.user_system_show_by_asset_tag', name="user-system-show-by-asset-tag"),
    #url(r'^show/(?P<object_id>\d+)/$', object_detail, info_dict, name="user-system-show"),
    url(r'^show/(?P<object_id>\d+)/$', 'views.user_system_show', name="user-system-show"),
    url(r'^delete/(?P<object_id>\d+)/$', 'views.unmanaged_system_delete', name='user-system-delete'),
    url(r'^csv/$', 'views.user_system_csv', name="user-system-csv"),
    url(r'^fillincsv/$', 'views.fillin_csv', name="user-system-fillin-csv"),

    url(r'^owners/new/$', 'views.owner_create', name="owner-new"),
    url(r'^owners/edit/(?P<object_id>\d+)/$', 'views.owner_edit', name="owner-edit"),
    url(r'^owners/$', 'views.owner_list', name="owner-list"),
    url(r'^owners/show/(?P<object_id>\d+)/$', 'views.owner_show', name="owner-show"),
    url(r'^owners/delete/(?P<object_id>\d+)/$', 'views.owner_delete', name='owner-delete'),
    url(r'^owners/upgradeable/$', object_list, owner_upgrade_info_dict, name="owner-upgradeable"),
    url(r'^owners/quicksearch/$', 'views.owners_quicksearch_ajax', name='owners-quicksearch'),

    url(r'^licenses/quicksearch/$', 'views.license_quicksearch_ajax', name='license-quicksearch'),
    #url(r'^licenses/new/$', 'views.license_new', name='license-new'),
    url(r'^licenses/new[/]$', 'views.license_new', name="license-new"),
    url(r'^licenses/type_search[/]$', 'views.license_type_search', name="license-type-search"),
    url(r'^licenses/version_search[/]$', 'views.license_version_search', name="license-version-search"),
    url(r'^licenses/edit/(?P<object_id>\d+)[/]$', 'views.license_edit', name="license-edit"),
    #url(r'^licenses/$', object_list, license_info_dict, name="license-list"),
    url(r'^licenses/$', 'views.license_index', name="license-list"),
    #url(r'^licenses/show/(?P<object_id>\d+)/$', object_detail, license_info_dict, name="license-show"),
    url(r'^licenses/show/(?P<object_id>\d+)/$', 'views.license_show', name="license-show"),
    #url(r'^licenses/delete/(?P<object_id>\d+)/$', delete_object, license_del_dict, name='license-delete'),
    url(r'^licenses/delete/(?P<object_id>\d+)/$', 'views.license_delete', name='license-delete'),
)
