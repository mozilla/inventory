from django.core.exceptions import PermissionDenied
from MozInvAuthorization.BaseACL import BaseACL
from settings import USER_SYSTEM_ALLOWED_DELETE
class UnmanagedSystemACL(BaseACL):
    def __init__(self, request):
        self.request = request
        if request.user.username and request.user.username != '':
            self.user = self.request.user.username
        else:
            self.user = self.request.META['REMOTE_USER']

    def check_delete(self, allowed = None):
        if allowed:
            allowed = allowed
        else:
            allowed = USER_SYSTEM_ALLOWED_DELETE
        self.check_for_permission(self.user, allowed)
