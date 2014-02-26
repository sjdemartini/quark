from django import forms
from django.conf import settings
from django.contrib.auth import forms as auth_forms
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.models import get_current_site
from django.core.mail import send_mail
from django.db.models import Q
from django.template import loader
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from quark.accounts.models import make_ldap_user
from quark.companies.models import CompanyRep
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
        # Call the ModelForm save method directly, since we are overriding the
        # Django UserCreationForm save() functionality here
        user = forms.ModelForm.save(self, commit=False)
        if USE_LDAP:
            # Create an entry in LDAP for this new user:
            ldap_utils.create_user(
                user.get_username(), self.cleaned_data['password1'], user.email,
                user.first_name, user.last_name)
            # Use the LDAPUser proxy model for this object
            make_ldap_user(user)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class UserChangeForm(UserFormMixin, auth_forms.UserChangeForm):
    pass


class AuthenticationForm(auth_forms.AuthenticationForm):
    """An AuthenticationForm that takes into account Company users."""
    def clean(self):
        """Performs the usual clean steps and also ensures that Company users
        and their Company's account expiration are taken into consideration.

        First, call the superclass method (which notably checks the password
        correctness and whether the given User is "active"). Then, if the user
        corresponds to a company representative account, this method performs
        the additional confirmation that the company account has not expired,
        raising a ValidationError if so.
        """
        cleaned_data = super(AuthenticationForm, self).clean()

        # TODO(sjdemartini): Move this logic to confirm_login_allowed once
        # upgraded Django 1.7
        try:
            # Try to get a company account for the given user
            company_rep = self.user_cache.companyrep
        except CompanyRep.DoesNotExist:
            # If the user is not a company, allow login
            return cleaned_data

        if company_rep.company.is_expired():
            raise forms.ValidationError(
                ('{}\'s subscription to this website has expired. '
                 'Please contact {} to arrange account renewal.'.format(
                     company_rep.company.name, settings.INDREL_ADDRESS)),
                code='expired'
            )

        return cleaned_data


class MakeLDAPUserMixin(object):
    """A mixin used in user forms that makes the user object for the form use
    the LDAPUser proxy model if USE_LDAP is true.

    Setting the user as an instance LDAPUser makes the object's methods act
    appropriately for when LDAP is enabled (such as set_password).
    """
    def __init__(self, *args, **kwargs):
        super(MakeLDAPUserMixin, self).__init__(*args, **kwargs)
        if USE_LDAP and self.user:
            make_ldap_user(self.user)


class SetPasswordForm(MakeLDAPUserMixin, auth_forms.SetPasswordForm):
    pass


class PasswordChangeForm(SetPasswordForm, auth_forms.PasswordChangeForm):
    pass


class AdminPasswordChangeForm(MakeLDAPUserMixin,
                              auth_forms.AdminPasswordChangeForm):
    pass


class PasswordResetForm(forms.Form):
    """A form for users to enter their username or email address and have a
    password reset email sent to them.

    Unlike the standard password reset form, note that this form accepts both
    username and email address, rather than just email address.

    The save method is primarily copied from django.contrib.auth.forms
    PasswordResetForm, though this reset-form allows for sending reset emails to
    users that have unusable passwords (as might be the case if passwords are
    only stored in LDAP). This is deliberately allowed, since the
    SetPasswordForm (used at the page linked to by the reset email) takes into
    account LDAP users, as needed. Also, while the Django form will send emails
    to multiple users if they all have the same email address on file, if
    multiple users are found here (due to having users with colliding email
    addresses), a validation error is raised.
    """
    username_or_email = forms.CharField(label='Username or email address')
    user_cache = None  # A cached user object, found during validation process

    def clean_username_or_email(self):
        entry = self.cleaned_data['username_or_email']

        # The username is case-sensitive, but the email address is not:
        lookup = Q(username__exact=entry) | Q(email__iexact=entry)

        user_model = get_user_model()
        try:
            self.user_cache = user_model._default_manager.get(
                lookup, is_active=True)
        except user_model.DoesNotExist:
            raise forms.ValidationError('Sorry, this user doesn\'t exist.')
        except user_model.MultipleObjectsReturned:
            raise forms.ValidationError('Unable to find distinct user.')
        return entry

    def save(self, domain_override=None,
             subject_template_name='registration/password_reset_subject.txt',
             email_template_name='accounts/password_reset_email.html',
             use_https=False, token_generator=default_token_generator,
             from_email=None, request=None):
        """
        Generate a one-use only link for resetting password and send it to the
        user.

        Use as defaults the built-in Django password_reset_subject template and
        the custom password_reset_email template.
        """
        if not domain_override:
            current_site = get_current_site(request)
            site_name = current_site.name
            domain = current_site.domain
        else:
            site_name = domain = domain_override

        # Get the user selected in the clean method:
        user = self.user_cache

        context = {
            'email': user.email,
            'domain': domain,
            'site_name': site_name,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'user': user,
            'token': token_generator.make_token(user),
            'protocol': 'https' if use_https else 'http',
        }
        subject = loader.render_to_string(subject_template_name, context)
        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())
        email = loader.render_to_string(email_template_name, context)
        send_mail(subject, email, from_email, [user.email])
