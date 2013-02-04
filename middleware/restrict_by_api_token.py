from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseForbidden
import base64
from django.contrib.auth.models import User
from systems.models import UserProfile


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

        self.orig_func = orig_func
        self.object = object
        self._using_token = False

    def _get_is_using_token(self, request):
        split = request.path.split("/")
        if split[1] == 'tokenapi' or split[2] == 'tokenapi':
            return True
        else:
            return False

    def __call__(self, request, *args, **kwargs):
        self._using_token = self._get_is_using_token(request)
        if self._using_token is True:
            try:
                the_part = base64.b64decode(request.META['HTTP_AUTHORIZATION'].split()[1]).split(':',1)
            except Exception, e:
                print e
            try:
                part1 = base64.b64decode(request.META['HTTP_AUTHORIZATION'].split()[1])
                username = part1.split(":")[0]
                password = part1.split(":")[1]
                user = User.objects.get(username__exact=username)
                user_profile= property(lambda u: UserProfile.objects.get_or_create(user=user)[0])
                print user_profile.api_key
                #user_profile = user.get_profile()

                try:
                    api_key = user_profile.api_key
                except:
                    return HttpResponseForbidden('There is no api key set for this account')

                if len(password) > 0 and password == api_key:
                    return self.orig_func(self, request, *args, **kwargs)
                else:
                    return HttpResponseForbidden('You are not authorized to view this resource')
            except Exception, e:
                print e
                return HttpResponseForbidden('You are not authorized to view this resource')

            return HttpResponseForbidden('You are not authorized to view this resource')
        else:
            #the_part = base64.b64decode(request.META['HTTP_AUTHORIZATION'].split()[1]).split(':',1)
            #the_part = the_part.partition(':')
            #username = the_part[0]
            #password = the_part[1]
            return self.orig_func(self, request, *args, **kwargs)
