from django.core.exceptions import PermissionDenied
from MozInvAuthorization.BaseKeyValueACL import BaseKeyValueACL
from settings import *
import systems.models as SystemModels
class KeyValueACL(BaseKeyValueACL):
    def __init__(self, request):
        self.request = request

    def check_delete(self, allowed = None):
        self.user = self.request.user
        if not self.user or self.user == '':
            raise PermissionDenied('You do not have permission to access this key scope')
        self.check_for_permission(self.user, allowed)
    
    def check_ip_not_exist_other_system(self, system, ip_address):
        keys = SystemModels.KeyValue.objects.filter(value=ip_address).exclude(system=system)
        if keys:
            raise Exception('IP Address Taken')
            #raise IPAddressTaken('You do not have permission to access this key scope')

    def _check_for_ownership(self, user, key):
        required_group = self._get_group_by_key(key)
        if required_group not in user.groups:
            raise PermissionDenied('You do not have permission to access this key scope')


    def _get_group_by_key(self, key):
        try:
            pass
            # Iterate through they list of keys to groups
            # if not in group
            #raise PermissionDenied('You do not have permission to access this key scope')
        except:
            # All is well, nothing to see here, move along
            pass
