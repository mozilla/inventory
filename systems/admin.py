from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin


class InvUserAdmin(UserAdmin):
    filter_horizontal = UserAdmin.filter_horizontal + ('groups',)


admin.site.unregister(User)
admin.site.register(User, InvUserAdmin)
