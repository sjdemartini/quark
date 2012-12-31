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

    list_display = ('username', 'preferred_name', 'last_name', 'is_admin',)
    list_filter = ('is_admin',)
    search_fields = ('username', 'first_name', 'last_name', 'preferred_name',)
    filter_horizontal = ()


class LDAPQuarkUserAdmin(QuarkUserAdmin):
    form = LDAPUserAdminChangeForm
    add_form = LDAPUserCreationForm


if settings.AUTH_USER_MODEL == 'auth.QuarkUser':
    admin.site.register(QuarkUser, QuarkUserAdmin)
elif settings.AUTH_USER_MODEL == 'auth.LDAPQuarkUser':
    admin.site.register(LDAPQuarkUser, LDAPQuarkUserAdmin)
