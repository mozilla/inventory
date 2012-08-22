"""
    file that we'll add all of the unit tests we want ran before every deploy
    ./manage.py test -s tests.tests
"""
from systems.tests import *
from api_v3.tests import *
from mozdns.tests.all import *
from core.tests.all import *
