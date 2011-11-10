import sys
import os
# This is an example settings/local.py file.
# These settings overrides what's in settings/base.py

# To extend any settings from settings/base.py here's an example:
#from . import base
#INSTALLED_APPS = base.INSTALLED_APPS + ['debug_toolbar']
STATIC_DOC_ROOT = '/home/jrm2k6/Documents/WebDev/playdoh-env/inventory/static'
API_ACCESS = ('GET','POST','PUT','DELETE')
USER_SYSTEM_ALLOWED_DELETE = ('jeremy.dagorn@gmail.com')
MEDIA_URL = '/static/'
_base = os.path.dirname(__file__)
site_root = '/home/jrm2k6/Documents/WebDev/playdoh-env/inventory'
sys.path.append(site_root)
sys.path.append(site_root + '/adapters')
sys.path.append(site_root + '/libs')
sys.path.append(site_root + '/modules')
sys.path.append(site_root + '/vendor')
DEBUG = False
TEMPLATE_DEBUG = DEBUG

STATIC_DOC_ROOT = os.path.join(_base, site_root + '/static')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'playdoh_app',
        'USER': 'root',
        'PASSWORD': 'root',
        'HOST': 'localhost',
        'PORT': '',
        'OPTIONS': {
            'init_command': 'SET storage_engine=InnoDB',
            'charset' : 'utf8',
            'use_unicode' : True,
        },
        'TEST_CHARSET': 'utf8',
        'TEST_COLLATION': 'utf8_general_ci',
    },
    # 'slave': {
    #     ...
    # },
}

INSTALLED_APPS = (                                        
    'django.contrib.sessions',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.admin',
    'piston',
    #'south',
    'systems',
    'user_systems',
    'build',
    'dhcp',
    'truth',
    'api',
    'api_v2',
    'reports',
)

# Recipients of traceback emails and other notifications.
ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)
MANAGERS = ADMINS

# Debugging displays nice error messages, but leaks memory. Set this to False
# on all server instances and True only for development.
DEBUG = TEMPLATE_DEBUG = True

# Is this a development instance? Set this to True on development/master
# instances and False on stage/prod.
DEV = True

# # Playdoh ships with sha512 password hashing by default. Bcrypt+HMAC is safer,
# # so it is recommended. Please read <https://github.com/fwenzel/django-sha2#readme>,
# # then switch this to bcrypt and pick a secret HMAC key for your application.
# PWD_ALGORITHM = 'bcrypt'
# HMAC_KEYS = {  # for bcrypt only
#     '2011-01-01': 'cheesecake',
# }

# Make this unique, and don't share it with anybody.  It cannot be blank.
SECRET_KEY = 'granule06'

# Uncomment these to activate and customize Celery:
# CELERY_ALWAYS_EAGER = False  # required to activate celeryd
# BROKER_HOST = 'localhost'
# BROKER_PORT = 5672
# BROKER_USER = 'playdoh'
# BROKER_PASSWORD = 'playdoh'
# BROKER_VHOST = 'playdoh'
# CELERY_RESULT_BACKEND = 'amqp'

## Log settings

# SYSLOG_TAG = "http_app_playdoh"  # Make this unique to your project.
# LOGGING = dict(loggers=dict(playdoh = {'level': logging.DEBUG}))


TEMPLATE_DIRS = (
    os.path.join(_base, 'templates'),
    site_root + '/templates'
)


ROOT_URLCONF = 'urls'
env.filters['url'] = jinja_url
env.globals['MEDIA_URL'] = MEDIA_URL
import logging
error = dict(level=logging.ERROR)
info = dict(level=logging.INFO)
debug = dict(level=logging.DEBUG)

LOGGING = {
    'loggers': {
        'product_details': error,
        'nose.plugins.manager': error,
        'django.db.backends': error,
        'elasticsearch': info,
        'inventory': debug,
    },
}
