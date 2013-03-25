from django.conf.urls.defaults import *
from django.core.urlresolvers import reverse
from django.shortcuts import redirect

# TODO, fix apache auth for oncall!
from oncall.views import getoncall, oncall

from models import ServerModel

from misc.generic_views import create_object, gen_mod_dict

urlpatterns = patterns('systems',
    (r'^quicksearch/$', 'views.system_quicksearch_ajax'),
    (r'^list_all_systems_ajax/$', 'views.list_all_systems_ajax'),
    (r'^get_network_adapters/(\d+)[/]$', 'views.get_network_adapters'),
    (r'^create_network_adapter/(\d+)[/]$', 'views.create_network_adapter'),
    (r'^get_expanded_key_value_store/(\d+)[/]$', 'views.get_expanded_key_value_store'),
    (r'^delete_network_adapter/(\d+)/(\d+)[/]$', 'views.delete_network_adapter'),
    (r'^save_network_adapter/(\d+)[/]$', 'views.save_network_adapter'),
    (r'^get_key_value_store/(\d+)[/]$', 'views.get_key_value_store'),
    (r'^create_key_value/(?P<id>\d+)[/]$', 'views.create_key_value'),
    (r'^delete_key_value/(?P<id>\d+)/(?P<system_id>\d+)[/]$', 'views.delete_key_value'),
    (r'^save_key_value/(\d+)[/]$', 'views.save_key_value'),
    (r'^new/$', 'views.system_new'),
    url(r'^show/(?P<id>\d+)[/]$', 'views.system_show'),
    url(r'^show/a(?P<id>\d+)[/]$', 'views.system_show_by_asset_tag'),
    (r'^edit/(\d+)[/]$', 'views.system_edit'),
    (r'^delete/(\d+)[/]$', 'views.system_delete'),
    url(r'^create_adapter/(?P<system_id>\d+)[/]$', 'views.create_adapter', name='system-network-adapter-create'),
    url(r'^get_next_intr_name/(?P<system_pk>\d+)[/]$', 'views.get_next_intr_name', name='system-network-adapter-name'),
    (r'^ajax_check_dupe_nic/(?P<system_id>\d+)/(?P<adapter_number>\d+)[/]$', 'views.check_dupe_nic'),
    (r'^system_auto_complete_ajax[/]$', 'views.system_auto_complete_ajax'),
    (r'^ajax_check_dupe_nic_name/(?P<system_id>\d+)/(?P<adapter_name>.*)[/]$', 'views.check_dupe_nic_name'),

    # TODO, Depricate these
    url(r'^oncall/$', oncall),
    url(r'^getoncall[/](?P<oncall_type>.*)[/]$', getoncall),

    url(r'^csv/$', 'views.system_csv', name="system-csv"),
    url(r'^releng_csv/$', 'views.system_releng_csv', name="system-csv"),
    url(r'^csv/import/$', 'views.csv_import', name='system-csv-import'),
    url(r'^racks/$', 'views.racks', name='system_rack-list'),
    url(r'^racks/delete/(?P<object_id>\d+)/$', 'views.rack_delete', name='rack-delete'),
    url(r'^racks/new/$', 'views.rack_new', name="system_rack-new"),
    url(r'^racks/edit/(?P<object_id>\d+)/$', 'views.rack_edit', name="system_rack-edit"),
    url(r'^racks/system/new/(?P<rack_id>\d+)/$', 'views.new_rack_system_ajax', name='racks-system-new'),
    url(r'^racks/elevation/(?P<rack_id>.*)[/]$', 'views.system_rack_elevation', name='system-rack-elevation'),
    url(r'^racks/bylocation/(?P<location>\d+)/$', 'views.racks_by_location', name='system-racks-by-location'),
    url(r'^server_models/new/$', create_object, gen_mod_dict(ServerModel, 'server_model-list'), name="server_model-new"),
    url(r'^server_models/edit/(?P<object_id>\d+)/$', 'views.server_model_edit', name="server_model-edit"),
    url(r'^server_models/$', 'views.server_model_list', name="server_model-list"),
    url(r'^server_models/create_ajax/$', 'views.server_model_create_ajax', name="server_model_create_ajax"),
    url(r'^server_models/list_ajax/$', 'views.server_model_list_ajax', name="server_model_list_ajax"),
    url(r'^operating_system/create_ajax/$', 'views.operating_system_create_ajax', name="server_model_create_ajax"),
    url(r'^operating_system/list_ajax/$', 'views.operating_system_list_ajax', name="server_model_list_ajax"),
    url(r'^server_models/show/(?P<object_id>\d+)/$', 'views.server_model_show', name="server_model-show"),
    #url(r'^server_models/delete/(?P<object_id>\d+)/$', delete_object, gen_del_dict(ServerModel, 'server_model-list'), name='server_model-delete'),
    url(r'^locations/new/$', 'views.location_new', name="location-new"),
    url(r'^locations/edit/(?P<object_id>\d+)/$', 'views.location_edit', name="location-edit"),
    url(r'^locations/$', 'views.location_list', name="location-list"),
    url(r'^locations/show/(?P<object_id>\d+)/$', 'views.location_show', name="location-show"),
    #url(r'^locations/delete/(?P<object_id>\d+)/$', delete_object, gen_del_dict(Location, 'location-list'), name='location-delete'),

    url(r'^allocations/new/$', 'views.allocation_new', name="allocation-new"),
    url(r'^allocations/edit/(?P<object_id>\d+)/$', 'views.allocation_edit',  name="allocation-edit"),
    url(r'^allocations/$', 'views.allocation_list', name="allocation-list"),
    url(r'^allocations/show/(?P<object_id>\d+)/$', 'views.allocation_show', name="allocation-show"),
)
