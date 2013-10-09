from django.contrib.auth.models import BaseUserManager
from django.contrib.auth.models import User

from quark.qldap import utils as ldap_utils


class LDAPUserManager(BaseUserManager):
    """Allows for creation of LDAP entries for users when creating users.

    Unlike the Django auth User, creating an LDAPUser requires a first and last
    name, which allows the method to create a corresponding LDAP entry.
    """
    def create_user(self, username, email, password,
                    first_name, last_name, **extra_fields):
        # Password must not be empty, but can be None for unusuable password
        if ((not username or not email or password == '' or
             not first_name or not last_name)):
            raise ValueError('Users must have username, email, password, '
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
            user.set_unusable_password()
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


class LDAPUser(User):
    """Overrides user model's password facilities.

    User passwords are stored only in LDAP and not in Django, so LDAP is used
    to set and check passwords. Django user objects will be set with unusable
    passwords.
    """
    # TODO(flieee): Also synchronizes username with LDAP on save
    # Requires quark.qldap

    objects = LDAPUserManager()

    class Meta(object):
        proxy = True
        verbose_name = 'LDAP User'

    def save(self, *args, **kwargs):
        """Only save the instance if user exists in LDAP."""
        if ldap_utils.username_exists(self.username):
            super(LDAPUser, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Delete the instance only if LDAP user deletion was successfull."""
        if ldap_utils.delete_user(self.username):
            super(LDAPUser, self).delete(*args, **kwargs)

    def check_password(self, raw_password):
        return ldap_utils.check_password(self.username, raw_password)

    def set_password(self, raw_password):
        self.set_unusable_password()
        ldap_utils.set_password(self.username, raw_password)
