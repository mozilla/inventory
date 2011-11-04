from django.contrib.auth.backends import RemoteUserBackend


class InvRemoteUserBackend(RemoteUserBackend):

    def configure_user(self, user):
        user.set_unusable_password()
        user.save()
        return user
