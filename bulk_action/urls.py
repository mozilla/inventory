from django.conf.urls.defaults import patterns, url
from bulk_action.views import (
    bulk_action_export, bulk_action_import, bulk_gather_vlan_pools
)

urlpatterns = patterns(
    'bulk_action',
    url(r'^export/', bulk_action_export, name='bulk-action-export'),
    url(r'^import/', bulk_action_import, name='bulk-action-import'),
    url(
        r'^gather_vlan_pools/', bulk_gather_vlan_pools,
        name='bulk-action-gather-vlan-pools'
    ),
)
