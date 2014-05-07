from django.conf import settings
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from quark.accounts.forms import AdminPasswordChangeForm
from quark.accounts.forms import UserChangeForm
from quark.accounts.forms import UserCreationForm
from quark.accounts.models import APIKey
from quark.accounts.models import LDAPUser
from quark.user_profiles.models import UserProfile


class APIKeyAdmin(admin.ModelAdmin):
    list_display = ('user', 'key')
    readonly_fields = ('user', 'key', 'created')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')


# Define an inline admin descriptor for the UserProfile model so that the
# UserProfile of a user can be edited on the same page.
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'user profile'


# Define a new User admin, extending the default UserAdmin
class UserAdminWithProfile(UserAdmin):
    add_form = UserCreationForm
    form = UserChangeForm
    change_password_form = AdminPasswordChangeForm
    inlines = (UserProfileInline, )
    list_display_links = ('username', 'first_name', 'last_name',)
    list_filter = ('is_staff', 'is_superuser', 'groups')
    add_fieldsets = (
        (None, {'classes': ('wide',),
                'fields': ('username', 'password1', 'password2',
                           'email', 'first_name', 'last_name')}),
    )

    def get_formsets(self, request, obj=None):
        """Prevent the inlines from being shown with the add form."""
        if obj is not None:
            # If the object exists already (i.e., this is the change form),
            # just perform the normal behavior
            for formset in super(UserAdminWithProfile, self).get_formsets(
                    request, obj):
                yield formset

        # Return nothing for the add form (i.e., if obj is None)


admin.site.register(APIKey, APIKeyAdmin)


# Re-register UserAdmin
user_model = get_user_model()
admin.site.unregister(user_model)

if getattr(settings, 'USE_LDAP', False):
    admin.site.register(LDAPUser, UserAdminWithProfile)
else:
    admin.site.register(user_model, UserAdminWithProfile)
