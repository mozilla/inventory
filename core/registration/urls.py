from django.conf.urls.defaults import patterns, url, include


urlpatterns = patterns('',
   url(r'static/', include('core.registration.static.urls')),
)
