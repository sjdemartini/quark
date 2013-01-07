from django.conf import settings
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from quark.auth.forms import LDAPUserAdminChangeForm
from quark.auth.forms import LDAPUserCreationForm
from quark.auth.forms import UserAdminChangeForm
from quark.auth.forms import UserCreationForm
from quark.auth.models import LDAPQuarkUser
from quark.auth.models import QuarkUser


class QuarkUserAdmin(UserAdmin):
    form = UserAdminChangeForm
    add_form = UserCreationForm

    list_display = ('username', 'preferred_name', 'last_name', 'is_superuser',)
    list_display_links = ('username', 'preferred_name', 'last_name',)
    list_filter = ('is_superuser', 'groups')
    fieldsets = (
        (None, {'fields': ('username', 'password',)}),
        ('Personal info', {'fields': ('first_name', 'middle_name', 'last_name',
                                      'preferred_name', 'email',)}),
        ('Permissions', {'fields': ('is_superuser',
                                    'groups', 'user_permissions',)}),
        ('Timestamps', {'classes': ('collapse',),
                        'fields': ('created',)}),
    )
    add_fieldsets = (
        (None, {'classes': ('wide',),
                'fields': ('username', 'password1', 'password2',
                           'email', 'first_name', 'middle_name', 'last_name',
                           'preferred_name',)}),
    )
    search_fields = ('username', 'email',
                     'first_name', 'last_name', 'preferred_name',)
    filter_horizontal = ()


class LDAPQuarkUserAdmin(QuarkUserAdmin):
    form = LDAPUserAdminChangeForm
    add_form = LDAPUserCreationForm


if settings.AUTH_USER_MODEL == 'auth.QuarkUser':
    admin.site.register(QuarkUser, QuarkUserAdmin)
elif settings.AUTH_USER_MODEL == 'auth.LDAPQuarkUser':
    admin.site.register(LDAPQuarkUser, LDAPQuarkUserAdmin)
