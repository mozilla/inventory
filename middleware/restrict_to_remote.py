from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseForbidden
from functools import wraps
from libs.ldap_lib import ldap_user_in_group

def allow_anyone(view_func):
    view_func.allow_anyone = True
    return view_func


def allow_build(view_func):
    view_func.allow_build = True
    return view_func

def sysadmin_only(view_func):
    view_func.sysadmin_only = True
    return view_func
def _in_group(user, group):
    try:
        g = user.groups.get(name=group)
        return True
    except ObjectDoesNotExist:
        return False
class LdapGroupRequired(object):
    def __init__(self, ldap_group, exclusive=False):
        self.ldap_group = ldap_group
        self.exclusive = exclusive

    def __call__(self, f):
        def wrapped_f(request, *args, **kwargs):
            if ldap_user_in_group(request.META['REMOTE_USER'],self.ldap_group) is True:
                if self.exclusive == False:
                    return f(request, *args, **kwargs)            
                else:
                    return HttpResponseForbidden('You do not have access to view this resource')
            else:
                if self.exclusive == False:
                    return HttpResponseForbidden('You do not have access to view this resource')
                else:
                    return f(request, *args, **kwargs)            
            #f(request, *args, **kwargs)            
        return wrapped_f

class RestrictToRemoteMiddleware:

    def process_view(self, request, view_func, view_args, view_kwargs):
        request.MOBILE = False
        if getattr(view_func, 'sysadmin_only', False) and _in_group(request.user, 'build'):
            return HttpResponseForbidden("You are not authorized to view this page")
        return
