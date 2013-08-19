from django import forms
from django.conf import settings
from django.contrib.auth.forms import UserChangeForm as AuthUserChangeForm
from django.contrib.auth.forms import UserCreationForm as AuthUserCreationForm


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


class UserCreationForm(UserFormMixin, AuthUserCreationForm):
    pass


class UserChangeForm(UserFormMixin, AuthUserChangeForm):
    pass
