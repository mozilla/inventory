from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseForbidden




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
def authenticated_api(function):
  def wrap(request, *args, **kwargs):
        print "Into Decorator"
        return request

  wrap.__doc__=function.__doc__
  wrap.__name__=function.__name__
  return wrap
