from piston.handler import BaseHandler, rc
from systems.models import UserProfile
import re
try:
    import json
except:
    from django.utils import simplejson as json
from mozilla_inventory.middleware.restrict_by_api_token import AuthenticatedAPI

from settings import API_ACCESS

from django.contrib.auth.models import User

class OncallHandler(BaseHandler):
    allowed_methods = API_ACCESS

    def read(self, request, oncall_type, display_type=None):
        oncall = ''
        if oncall_type == 'desktop':
            if display_type == 'email':
                result = User.objects.select_related().filter(userprofile__current_desktop_oncall=1)[0]
                oncall = {'user':result.username, 'pager_type': result.get_profile().pager_type, 'epager_address': result.get_profile().epager_address, 'pager_number': result.get_profile().pager_number}
            elif display_type == 'irc_nick':
                result = User.objects.select_related().filter(userprofile__current_desktop_oncall=1)[0]
                oncall = {'user':result.get_profile().irc_nick, 'pager_type': result.get_profile().pager_type, 'epager_address': result.get_profile().epager_address, 'pager_number': result.get_profile().pager_number}
            elif display_type == 'all':
                oncall = []
                list = User.objects.select_related().filter(userprofile__is_desktop_oncall=1)
                for u in list:
                    oncall.append({'user':u.get_profile().irc_nick, 'pager_type': u.get_profile().pager_type, 'pager_number': u.get_profile().pager_number})
        elif oncall_type == 'sysadmin':
            if display_type == 'email':
                result = User.objects.select_related().filter(userprofile__current_sysadmin_oncall=1)[0]
                oncall = {'user':result.username, 'pager_type': result.get_profile().pager_type, 'epager_address': result.get_profile().epager_address, 'pager_number': result.get_profile().pager_number}
            elif display_type == 'irc_nick':
                result = User.objects.select_related().filter(userprofile__current_sysadmin_oncall=1)[0]
                oncall = {'user':result.get_profile().irc_nick, 'pager_type': result.get_profile().pager_type, 'epager_address': result.get_profile().epager_address, 'pager_number': result.get_profile().pager_number}
            elif display_type == 'all':
                oncall = []
                list = User.objects.select_related().filter(userprofile__is_sysadmin_oncall=1)
                for u in list:
                    oncall.append({'user':u.get_profile().irc_nick, 'pager_type': u.get_profile().pager_type, 'pager_number': u.get_profile().pager_number})
        return oncall
    def update(self, request, oncall_type = None, display_type=None):
        user = display_type
        from django.db import connection, transaction
    	if request.method == 'PUT':
            if oncall_type == 'setdesktop':
                cursor = connection.cursor()
                cursor.execute("UPDATE `user_profiles` set `current_desktop_oncall` = 0")
                transaction.commit_unless_managed()
                if re.match("^[a-zA-Z0-9._%-]+@[a-zA-Z0-9._%-]+.[a-zA-Z]{2,6}$", user):
                    new_oncall = User.objects.get(username=user)
                else:
                    new_oncall = User.objects.get(userprofile__irc_nick=user)
                new_oncall.get_profile().current_desktop_oncall = 1
                new_oncall.get_profile().save()
                new_oncall.save()
                resp = rc.ALL_OK
                return resp
                
            elif oncall_type == 'setsysadmin':
                cursor = connection.cursor()
                cursor.execute("UPDATE `user_profiles` set `current_sysadmin_oncall` = 0")
                transaction.commit_unless_managed()
                if re.match("^[a-zA-Z0-9._%-]+@[a-zA-Z0-9._%-]+.[a-zA-Z]{2,6}$", user):
                    new_oncall = User.objects.get(username=user)
                else:
                    new_oncall = User.objects.get(userprofile__irc_nick=user)
                new_oncall.get_profile().current_sysadmin_oncall = 1
                new_oncall.get_profile().save()
                new_oncall.save()
                resp = rc.ALL_OK
                return resp

            else:
                resp = rc.NOT_FOUND
                return resp
    def delete(self, request, oncall_type=None):
        pass
