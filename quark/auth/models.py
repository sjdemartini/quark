from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.db.models import get_model
from django.utils import timezone

from quark.qldap import utils as ldap_utils

try:
    from django.contrib.auth import get_user_model
except ImportError:
    # TODO(flieee): Remove try/except when django 1.5 is deployed
    def get_user_model():
        # Lazy loading of setting variable
        from django.conf import settings
        user = get_model(*settings.AUTH_USER_MODEL.split('.', 1))
        if user is None:
            raise NameError(
                'User model not found: %s' % settings.AUTH_USER_MODEL)
        return user


class QuarkUserManager(BaseUserManager):
    def create_user(self, username, email, password,
                    first_name, last_name, **extra_fields):
        # Password must not be empty, but can be None for unusuable password
        if ((not username or not email or password == '' or
             not first_name or not last_name)):
            raise ValueError('Users must have username, email, password, '
                             'first name and last name')

        user = self.model(
            username=username,
            email=self.normalize_email(email),
            first_name=first_name,
            last_name=last_name,
            **extra_fields)

        # Providing password=None is equivalent to set_unusable_password
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, username, email, password,
                         first_name, last_name, **extra_fields):
        return self.create_user(username, email, password,
                                first_name, last_name,
                                is_superuser=True, **extra_fields)


class QuarkUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=30, unique=True, db_index=True)
    email = models.EmailField(
        max_length=255,
        db_index=True,
        unique=True,
        verbose_name='email address')
    # Names
    first_name = models.CharField(
        max_length=64,
        db_index=True,
        help_text='Your official first or given name')
    middle_name = models.CharField(max_length=64, blank=True)
    last_name = models.CharField(max_length=64, db_index=True)
    preferred_name = models.CharField(
        max_length=64,
        db_index=True,
        help_text='What would you like us to call you? (Optional)')

    created = models.DateTimeField(default=timezone.now)

    objects = QuarkUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Quark User'

    def save(self, *args, **kwargs):
        if not self.preferred_name:
            self.preferred_name = self.first_name
        super(QuarkUser, self).save(*args, **kwargs)

    def get_full_name(self):
        if self.middle_name:
            return '%s %s %s' % (
                self.first_name, self.middle_name, self.last_name)
        else:
            return '%s %s' % (self.first_name, self.last_name)

    def get_common_name(self):
        return '%s %s' % (self.preferred_name, self.last_name)

    def get_short_name(self):
        return self.preferred_name or self.first_name

    @property
    def is_staff(self):
        # TODO(flieee): True if user is in some sort of IT role also
        return self.is_superuser


class LDAPQuarkUserManager(QuarkUserManager):
    """
    Creates LDAP entries for users when creating users
    """
    def create_user(self, username, email, password,
                    first_name, last_name, **extra_fields):
        norm_email = self.normalize_email(email)
        if ldap_utils.create_user(username, password, norm_email,
                                  first_name, last_name):
            # Create a QuarkUser with an unusable password (None)
            return super(LDAPQuarkUserManager, self).create_user(
                username, email, password,
                first_name, last_name, **extra_fields)
        else:
            # Failed to create a new user entry in LDAP
            return None

    def create_superuser(self, username, email, password,
                         first_name, last_name, **extra_fields):
        norm_email = self.normalize_email(email)
        if ldap_utils.create_user(username, password, norm_email,
                                  first_name, last_name):
            # Create a QuarkUser with an unusable password (None)
            return super(LDAPQuarkUserManager, self).create_superuser(
                username, email, password,
                first_name, last_name, **extra_fields)
        else:
            # Failed to create a new user entry in LDAP
            return None


class LDAPQuarkUser(QuarkUser):
    """
    Overrides default custom user's password facilities.
    TODO(flieee): Also synchronizes username with LDAP on save
    Requires quark.qldap
    """
    objects = LDAPQuarkUserManager()

    class Meta:
        proxy = True
        verbose_name = 'LDAP Quark User'

    def save(self, *args, **kwargs):
        """Only save the instance if user exists in LDAP"""
        if ldap_utils.username_exists(self.username):
            super(LDAPQuarkUser, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Only delete the instance if LDAP user deletion was successfull"""
        if ldap_utils.delete_user(self.username):
            super(LDAPQuarkUser, self).save(*args, **kwargs)

    def check_password(self, raw_password):
        return ldap_utils.check_password(self.username, raw_password)

    def set_password(self, raw_password):
        self.set_unusable_password()
        ldap_utils.set_password(self.username, raw_password)


# pylint: disable=C0103
User = get_user_model()
