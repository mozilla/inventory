from tastypie.authentication import BasicAuthentication


class AuthenticationByMethod(BasicAuthentication):
    '''Use when authentication requirement varies by the method being used.'''

    def __init__(self, *args, **kwargs):
        '''Constructor. Expects a list of HTTP methods which are allowed
        WITHOUT authentication, all other methods will require
        authentication'''

        self.allowed_methods = list(args)
        super(AuthenticationByMethod, self).__init__()

    def is_authenticated(self, request, **kwargs):
        method_is_allowed = request.method in self.allowed_methods
        if request.user.is_authenticated() or method_is_allowed:
            return True
        else:
            return super(AuthenticationByMethod, self).is_authenticated(
                request, **kwargs)
