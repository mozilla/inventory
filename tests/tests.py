"""
    file that we'll add all of the unit tests we want ran before every deploy
    ./manage.py test -s tests.tests
"""
from systems.tests import *  # noqa
from dhcp.tests import *  # noqa
from api_v3.tests import *  # noqa
from mozdns.tests.all import *  # noqa
from core.tests.all import *  # noqa
from oncall.tests import *  # noqa
from mcsv.tests import *  # noqa
from bulk_action.tests import *  # noqa
