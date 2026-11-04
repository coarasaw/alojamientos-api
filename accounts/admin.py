from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Rol", {"fields": ("rol",)}),)
    list_display = ("username", "email", "rol", "is_staff")
