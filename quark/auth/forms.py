from django import forms
from django.conf import settings
from django.contrib.auth.forms import ReadOnlyPasswordHashField

from quark.auth.models import LDAPQuarkUser
from quark.auth.models import QuarkUser


class UserCreationForm(forms.ModelForm):
    username = forms.RegexField(
        regex=settings.VALID_USERNAME,
        help_text=settings.USERNAME_HELPTEXT)
    password1 = forms.CharField(
        label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(
        label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = QuarkUser

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if not password1 or not password2 or password1 != password2:
            raise forms.ValidationError('Passwords must match')
        return password2

    def save(self, commit=True, **kwargs):
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save(**kwargs)
        return user


class UserAdminChangeForm(forms.ModelForm):
    username = forms.RegexField(
        regex=settings.VALID_USERNAME,
        help_text=settings.USERNAME_HELPTEXT)
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = QuarkUser

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial['password']


class LDAPUserCreationForm(UserCreationForm):
    class Meta:
        model = LDAPQuarkUser


class LDAPUserAdminChangeForm(UserAdminChangeForm):
    class Meta:
        model = LDAPQuarkUser
