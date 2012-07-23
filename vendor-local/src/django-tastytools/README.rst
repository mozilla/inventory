=================
django-tastytools
=================

Useful tools for developing REST services with django-tastypie

Requirements
============

Required
--------

* django-tastypie (http://django-tastypie.readthedocs.org/)


What iss It Look Like?
======================

Asuming you have a tastypie implemented api, a basic example looks like::

    # myapp/api/tools.py
    # ============
    from tastytools.api import Api
    from resources import MyModelResource, AnotherResource, YetAnotherResource

    api = Api()
    api.register(MyModelResource)
    api.register(resources=[AnotherResource, YetAnotherResource])


    # urls.py
    from tastypie.api import Api
    from my_app.api.resources import MyModelResource

    api_name = 'v1'
    v1_api = Api(api_name=api_name)
    v1_api.register(MyModelResource())

    urlpatterns = patterns('',
      # ...more URLconf bits here...
      # Then add:
      (r'^tastytools/', include('tastytools.urls'), {'api_name': api_name}),
    )

That gets you a basic automatic documentation for your api at /tastytools/doc/

You can find more in the documentation at
http://tastytools.readthedocs.org/.


What is tastytools?
===================
Useful tools for developing REST services with django-tastypie
