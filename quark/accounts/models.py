from django.contrib import auth
from django.contrib.auth.models import BaseUserManager
from django.core.exceptions import ValidationError

from quark.qldap import utils as ldap_utils


class LDAPUserManager(BaseUserManager):
    """Allows for creation of LDAP entries for users when creating users.

    Unlike the Django auth User, creating an LDAPUser requires a first and last
    name, which allows the method to create a corresponding LDAP entry.

    Note: This LDAPUserManager assumes that the AUTH_USER_MODEL has username,
    email, password, first name, and last name as fields on the model. This
    Manager should be adjusted for specific User implementations as needed.
    """
    def create_user(self, username, email, password,
                    first_name, last_name, **extra_fields):
        # Password must not be empty, but can be None for unusuable password
        if (not username or not email or password == '' or
                not first_name or not last_name):
            raise ValidationError('Users must have username, email, password, '
                                  'first name and last name')
        norm_email = self.normalize_email(email)
        if ldap_utils.create_user(username, password, norm_email, first_name,
                                  last_name):
            # Create a user with an unusable password (None) in Django
            user = self.model(
                username=username,
                email=self.normalize_email(email),
                first_name=first_name,
                last_name=last_name,
                **extra_fields)
            super(self.model, user).set_unusable_password()
            user.save()
            return user
        else:
            # Failed to create a new user entry in LDAP
            return None

    def create_superuser(self, username, email, password,
                         first_name, last_name, **extra_fields):
        return self.create_user(username, email, password,
                                first_name, last_name,
                                is_superuser=True, **extra_fields)


class LDAPUser(auth.get_user_model()):
    """Overrides user model's password facilities.

    User passwords are stored only in LDAP and not in Django, so LDAP is used
    to set and check passwords. Django user objects will be set with unusable
    passwords.

    The LDAPUser cannot be set as the AUTH_USER_MODEL, as it is a proxy model
    for the AUTH_USER_MODEL.
    """
    # TODO(flieee): Also synchronizes username with LDAP on save
    # Requires quark.qldap

    objects = LDAPUserManager()

    class Meta(object):
        proxy = True
        verbose_name = 'LDAP User'

    def save(self, *args, **kwargs):
        """Only save the instance if user exists in LDAP."""
        if not ldap_utils.username_exists(self.get_username()):
            raise ValidationError(
                'There is no user with username {} in LDAP, so the user cannot '
                'be saved. If you are trying to create a user, please use the '
                'LDAPUserManager create_user method.'.format(
                    self.get_username()))
        super(LDAPUser, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Delete the instance only if LDAP user deletion was successfull."""
        if ldap_utils.delete_user(self.get_username()):
            super(LDAPUser, self).delete(*args, **kwargs)

    def check_password(self, raw_password):
        return ldap_utils.check_password(self.get_username(), raw_password)

    def has_usable_password(self):
        return ldap_utils.has_usable_password(self.get_username())

    def set_password(self, raw_password):
        super(LDAPUser, self).set_unusable_password()
        ldap_utils.set_password(self.get_username(), raw_password)

    def set_unusable_password(self):
        ldap_utils.set_password(self.get_username(), None)


def make_ldap_user(user):
    """Sets the user model for the given user to be the LDAPUser proxy model.
    """
    # Change the user class to the proxy model LDAPUser
    user.__class__ = LDAPUser
