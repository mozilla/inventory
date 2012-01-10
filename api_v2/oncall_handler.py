from piston.handler import BaseHandler, rc
from systems.models import UserProfile
import re
try:
    import json
except:
    from django.utils import simplejson as json
from settings import API_ACCESS

from django.contrib.auth.models import User

class OncallHandler(BaseHandler):
    allowed_methods = API_ACCESS

    def read(self, request, oncall_type):

        if oncall_type == 'desktop':
            oncall = User.objects.select_related().filter(userprofile__current_desktop_oncall=1)[0].username
        if oncall_type == 'sysadmin':
            oncall = User.objects.select_related().filter(userprofile__current_sysadmin_oncall=1)[0].username
        return oncall
    def update(self, request, oncall_type=None):
        pass
    	if request.method == 'PUT':
            return resp

    def delete(self, request, oncall_type=None):
        pass
