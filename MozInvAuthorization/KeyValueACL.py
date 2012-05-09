from django.core.exceptions import PermissionDenied
from MozInvAuthorization.BaseKeyValueACL import BaseKeyValueACL
from settings import 
class KeyValueACL(BaseKeyValueACL):
    def __init__(self, request):
        self.request = request

    def check_delete(self, allowed = None):
        self.user = self.request.user
        if not self.user or self.user == '':
            raise PermissionDenied('You do not have permission to access this key scope')
        self.check_for_permission(self.user, allowed)

    def _check_for_ownership(self, user, key):
        required_group = self._get_group_by_key(key)
        if required_group not in user.groups:
            raise PermissionDenied('You do not have permission to access this key scope')


    def _get_group_by_key(self, key):
        try:
            # Iterate through they list of keys to groups
            # if not in group
            #raise PermissionDenied('You do not have permission to access this key scope')
        except:
            # All is well, nothing to see here, move along
            pass
