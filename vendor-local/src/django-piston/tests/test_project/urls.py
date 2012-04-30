from django.conf.urls.defaults import *
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'api/', include('test_project.apps.testapp.urls')),
    url(r'^admin/', include(admin.site.urls)),
)
