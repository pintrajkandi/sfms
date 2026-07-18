from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User

UserAdmin.fieldsets = UserAdmin.fieldsets + (("SFMS", {"fields": ("role", "phone")}),)
admin.site.register(User, UserAdmin)
