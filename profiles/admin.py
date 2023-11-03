from django import forms
from django.contrib import admin
from django.utils.safestring import mark_safe
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .forms import UserRegisterForm
from .models import CustomUser, Profile


class ProfileAdmin(admin.StackedInline):
    model = Profile
    can_delete = False
    extra = 0
    max_num = 1


class CustomUserAdmin(UserAdmin):
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "email", "password1", "password2", "email_verify"),
            },
        ),
    )

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "email", "email_verify")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    list_display = ("username", "email", "first_name", "last_name", "is_staff", "email_verify")

    add_form = UserRegisterForm

    inlines = (ProfileAdmin, )




admin.site.register(CustomUser, CustomUserAdmin)
