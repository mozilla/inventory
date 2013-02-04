from django.conf.urls.defaults import *
urlpatterns = patterns('build',
    url(r'^$', 'views.build_list', name='build-list'),
    url(r'^quicksearch/$', 'views.quicksearch_ajax', name='build-quicksearch'),
    url(r'^show/(\d+)/$', 'views.build_show', name='build-show'),
    url(r'^edit/(\d+)/$', 'views.build_edit', name='build-edit'),
    url(r'^bulk/$', 'views.build_bulk', name='build-bulk-edit'),
    url(r'^csv/$', 'views.build_csv', name='build-csv'),
)
