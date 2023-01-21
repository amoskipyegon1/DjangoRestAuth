from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from .forms import UserChangeForm, UserCreationForm

admin.site.unregister(Group)

User = get_user_model()


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm

    list_display = ["emailAddress", "firstName", "lastName", "is_admin"]
    list_filter = ("is_admin",)

    fieldsets = (
        ("Authentication", {"fields": ("emailAddress",)}),
        ("Permissions", {"fields": ("is_admin",)}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("emailAddress", "firstName", "password1", "password2"),
            },
        ),
    )

    search_fields = ("emailAddress",)
    ordering = ("emailAddress",)
    filter_horizontal = ()
