from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.db import models
from systems.models import UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
     
class InvUserAdmin(UserAdmin):
    filter_horizontal = UserAdmin.filter_horizontal + ('groups',)
    inlines = [UserProfileInline]


admin.site.unregister(User)
admin.site.register(User, InvUserAdmin)
admin.site.register(UserProfile)
