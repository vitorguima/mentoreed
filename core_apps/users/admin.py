from django.contrib import admin
from django.contrib.admin.sites import site
from unfold.admin import ModelAdmin

from .models import User

if site.is_registered(User):
    site.unregister(User)


@admin.register(User)
class UserAdmin(ModelAdmin):
    """
    Admin interface for the custom User model.
    This class can be extended to customize the admin interface.
    """

    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "is_active",
    )
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("username",)
    list_filter = ("is_staff", "is_active")
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "email")}),
        (
            "Permissions",
            {"fields": ("is_staff", "is_active", "groups", "user_permissions")},
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
