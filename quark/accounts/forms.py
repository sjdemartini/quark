from django import forms
from django.conf import settings
from django.contrib.auth import forms as auth_forms

from quark.accounts.models import make_ldap_user
from quark.qldap import utils as ldap_utils


USE_LDAP = getattr(settings, 'USE_LDAP', False)


class UserFormMixin(object):
    """Change the username regex and require user fields."""
    def __init__(self, *args, **kwargs):
        super(UserFormMixin, self).__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['username'] = forms.RegexField(
            regex=settings.VALID_USERNAME,
            help_text=settings.USERNAME_HELPTEXT)


class UserCreationForm(UserFormMixin, auth_forms.UserCreationForm):
    def clean_username(self):
        username = super(UserCreationForm, self).clean_username()
        if USE_LDAP and ldap_utils.username_exists(username):
            raise forms.ValidationError(
                self.error_messages['duplicate_username'],
                code='duplicate_username',
            )
        return username

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        if USE_LDAP:
            # Create an entry in LDAP for this new user:
            ldap_utils.create_user(
                user.get_username(), self.cleaned_data["password1"], user.email,
                user.first_name, user.last_name)
            # Use the LDAPUser proxy model for this object
            make_ldap_user(user)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(UserFormMixin, auth_forms.UserChangeForm):
    pass


class MakeLDAPUserMixin(object):
    """A mixin used in user forms that makes the user object for the form use
    the LDAPUser proxy model if USE_LDAP is true.

    Setting the user as an instance LDAPUser makes the object's methods act
    appropriately for when LDAP is enabled (such as set_password).
    """
    def __init__(self, *args, **kwargs):
        super(MakeLDAPUserMixin, self).__init__(*args, **kwargs)
        if USE_LDAP:
            make_ldap_user(self.user)


class SetPasswordForm(MakeLDAPUserMixin, auth_forms.SetPasswordForm):
    pass


class PasswordChangeForm(SetPasswordForm, auth_forms.PasswordChangeForm):
    pass


class AdminPasswordChangeForm(MakeLDAPUserMixin,
                              auth_forms.AdminPasswordChangeForm):
    pass
