from django.conf.urls.defaults import patterns, url
from bulk_action.views import bulk_action_export, bulk_action_import

urlpatterns = patterns(
    'bulk_action',
    url(r'^export/', bulk_action_export, name='bulk-action-export'),
    url(r'^import/', bulk_action_import, name='bulk-action-import'),
)
