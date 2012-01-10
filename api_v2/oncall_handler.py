from piston.handler import BaseHandler, rc
from systems.models import UserProfile
import re
try:
    import json
except:
    from django.utils import simplejson as json
from middleware.restrict_by_api_token import AuthenticatedAPI

from settings import API_ACCESS

from django.contrib.auth.models import User

class OncallHandler(BaseHandler):
    allowed_methods = API_ACCESS

    @AuthenticatedAPI
    def read(self, request, oncall_type):

        if oncall_type == 'desktop':
            oncall = User.objects.select_related().filter(userprofile__current_desktop_oncall=1)[0].username
        elif oncall_type == 'sysadmin':
            oncall = User.objects.select_related().filter(userprofile__current_sysadmin_oncall=1)[0].username
        elif oncall_type == 'listsysadmin':
            oncall = []
            list = User.objects.select_related().filter(userprofile__is_sysadmin_oncall=1)
            for u in list:
                oncall.append(u.username)
        elif oncall_type == 'listdesktop':
            oncall = []
            list = User.objects.select_related().filter(userprofile__is_desktop_oncall=1)
            for u in list:
                oncall.append(u.username)
        return oncall
    def update(self, request, oncall_type=None):
        pass
    	if request.method == 'PUT':
            return resp

    def delete(self, request, oncall_type=None):
        pass
