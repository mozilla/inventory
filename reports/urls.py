from django.conf.urls.defaults import *
from django.views.generic.list_detail import object_detail, object_list
from systems.models import ServerModel, Location, Allocation, SystemRack, KeyValue

from misc.generic_views import create_object, update_object, delete_object, gen_mod_dict, gen_info_dict, gen_del_dict

urlpatterns = patterns('reports',
    url(r'^$', 'views.report_home', name="report-home"),
    #url(r'^server_models/delete/(?P<object_id>\d+)/$', delete_object, gen_del_dict(ServerModel, 'server_model-list'), name='server_model-delete'),

)
