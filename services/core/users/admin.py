from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "is_staff", "created_at", "id")
    list_filter = ("is_staff", "is_superuser", "is_active", "groups", "created_at")
    search_fields = ("username", "email")
    readonly_fields = ("created_at", "updated_at", "id")
    fieldsets = tuple(UserAdmin.fieldsets or ()) + (("System Info", {"fields": ("created_at", "updated_at")}),)
