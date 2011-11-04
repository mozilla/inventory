from django.conf.urls.defaults import *
from django.views.generic.list_detail import object_detail, object_list

from misc.generic_views import create_object, update_object, delete_object, gen_mod_dict, gen_info_dict, gen_del_dict

urlpatterns = patterns('truth',
    url(r'^$', 'views.index', name='truth-list'),
    url(r'^list_all_keys_ajax[/]$', 'views.list_all_keys_ajax', name='truth-list-all-keys-ajax'),
    url(r'^edit/(\d+)[/]$', 'views.edit', name='truth-list-edit'),
    url(r'^create/$', 'views.create', name='truth-list-create'),
    url(r'^delete/(\d+)[/]$', 'views.delete', name='truth-list-delete'),
    url(r'^get_key_value_store/(\d+)[/]$', 'views.get_key_value_store', name='truth-list-edit'),
    url(r'^create_key_value/(\d+)[/]$', 'views.create_key_value', name='truth-list-create'),
    url(r'^save_key_value/(\d+)[/]$', 'views.save_key_value', name='truth-list-save'),
    url(r'^delete_key_value/(\d+)/(\d+)[/]$', 'views.delete_key_value', name='truth-list-delete'),
)
