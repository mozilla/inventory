from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseForbidden
import base64



class RestrictByToken:
    supports_object_permissions = False
    supports_anonymous_user = False
    def authenticate(self, username=None, password=None, token=None):
        print "The path is %s" % request.path
        username = None
        password = None
        token = None
        try:
            the_part = base64.b64decode(request.META['HTTP_AUTHORIZATION'].split()[1]).split(':',1)
            username = the_part[0]
            password = the_part[1]
        except:
            username = request.user
            if 'token' in request.GET:
                token = request.GET['token']



        try:
            user = authenticate(username=username, token=token, password=password)
        except:
            return HttpResponseForbidden('You are not authorized to view this resource')
        return None

    def get_user(self, user_id):
            try:
                return User.objects.get(pk=user_id)
            except User.DoesNotExist:
                return None

class AuthenticatedAPI(object):
    def __init__(self, orig_func):

        print "Init called"
        self.orig_func = orig_func
        self.object = object
        self._using_token = False

    def _get_is_using_token(self, request):
        split = request.path.split("/")
        print split
        if split[1] == 'tokenapi' or split[2] == 'tokenapi':
            return True
        else:
            return False

    def __call__(self, request, *args, **kwargs):
        self._using_token = self._get_is_using_token(request)
        if self._using_token is True:
            return HttpResponseForbidden('You are not authorized to view this resource')
        else:
            #the_part = base64.b64decode(request.META['HTTP_AUTHORIZATION'].split()[1]).split(':',1)
            #the_part = the_part.partition(':')
            #username = the_part[0]
            #password = the_part[1]
            return self.orig_func(self, request, *args, **kwargs)
