from django.conf.urls.defaults import *
from django.views.generic.list_detail import object_detail, object_list

from misc.generic_views import create_object, update_object, delete_object, gen_mod_dict, gen_info_dict, gen_del_dict

urlpatterns = patterns('dhcp',
    url(r'^show/$', 'views.showall', name='dhcp-list'),
    url(r'^showfile/(.*)[/]$', 'views.showfile', name='dhcp-show-file'),
    url(r'^override/(.*)[/]$', 'views.override_file', name='dhcp-show-override'),
    url(r'^new/$', 'views.new'),
    url(r'^edit/(.*)[/]$', 'views.edit'),
    url(r'^edit/$', 'views.create'),
    url(r'^delete/(.*)/$', 'views.delete'),
)
