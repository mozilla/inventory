from django.core.exceptions import PermissionDenied
class BaseACL(object):
    request = None
    user = None

    def __init__(self, request):
        self.request = request
        self.user = request.user.username

    def check_create(self, allowed = None):
        pass

    def check_read(self, allowed = None):
        pass

    def check_update(self, allowed = None):
        pass
    def check_delete(self, allowed = None):
        pass

    """
        check_for_permission currently just looks at a setting var
        main purpose for existance is to allow easy extension to look for group membership via ldap
    """
    def check_for_permission(self, user, acl_list):
        if user is None or user == '' or user not in acl_list:
            raise PermissionDenied('You do not have permission to delete this license.')
