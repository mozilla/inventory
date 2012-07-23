from django.conf.urls.defaults import *
from api import Api
from example import *

test_api = Api()
test_api.register(modules=[resources1, resources2, resources3]   )

urlpatterns = patterns('',
    (r'^api/', include(test_api.urls)),
    url(r'^test', 'nothing', name='test_url'),
)