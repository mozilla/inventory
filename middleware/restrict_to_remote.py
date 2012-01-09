from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseForbidden


def allow_anyone(view_func):
    view_func.allow_anyone = True
    return view_func


def allow_build(view_func):
    view_func.allow_build = True
    return view_func


def _in_group(user, group):
    try:
        g = user.groups.get(name=group)
        return True
    except ObjectDoesNotExist:
        return False


class RestrictToRemoteMiddleware:

    def process_view(self, request, view_func, view_args, view_kwargs):
        request.MOBILE = False
        
        if settings.DEV == True:
            return None
        ## Check if connecting to /tokenapi.
        ## IF so then we don't need to check the rest of this stuff. The API will validate credentials

        path_list = request.path.split('/')
        if path_list[1] == 'tokenapi' or path_list[2] == 'tokenapi':
            return None

        try:
            if request.META['REMOTE_ADDR'] == '127.0.0.1':
                return None
        except:
            pass
        if not settings.REMOTE_LOGINS_ON:
            return None

        if not request.user.is_authenticated():
            request.read_only = True

        if request.user.is_superuser or _in_group(request.user, 'ops'):
            return None

        if getattr(view_func, 'allow_build', False) and _in_group(request.user, 'build'):
            return None

        if getattr(view_func, 'allow_anyone', False):
            return None

        return HttpResponseForbidden("You are not authorized to view this page")
