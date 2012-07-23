Welcome to tastytools's documentation!
======================================

Tastytools is a set for usefull tools to develop a quality tastypie webservice
API.

It's main features are automatic documentation and the generation of Hygiene
tests (tests that ensure the pressence of certain features that that do not
give positive satisfaction, though dissatisfaction results from their absence).
For example it tests the pressence of help fields
An example in the case of an API, is a help text on the fields

.. toctree::
   :maxdepth: 2

   tutorial

Quick Start
===========

Assuming you have a tastypie api and have already read the `tastypie docs`_:

1. Add ``tastytools`` to ``INSTALLED_APPS``.
2. Create an file in ``<my_app>/api/tools.py``, and move the tastypi api definition from the urls.py file to it::

    from tastytools.api import Api
    from <my_app>.api.resources import MyModelResource
    from <my_app>.api.resources import AnoterResource, YetAnotherResource

    api = Api()
    api.register(MyModelResource)
    api.register(resources=[AnotherResource, YetAnotherResource])

3. Then import the api to your urls root file::

    from my_app.api.tools import api

    urlpatterns = patterns('',
      # ...more URLconf bits here...
      (r'^api/', include(api.urls)),
      # Then add:
      (r'^tastytools/', include('tastytools.urls'), {'api_name': api.api_name}),
    )

4. got to http://localhost:8000/tastytools/v1/.

As you can see, now you have documentation for anyone who wants to consume
your api resources!

Requirements
============

Tastytools requires Tastypie to work. If you use Pip_, you can install
the necessary bits via the included ``requirements.txt``:

* django-tastypie (http://django-tastypie.readthedocs.org/)

.. _Pip: http://pip.openplans.org/
.. _`tastypie docs`: http://django-tastypie.readthedocs.org/en/latest/index.html
