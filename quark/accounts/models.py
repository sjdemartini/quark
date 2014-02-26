from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import BaseUserManager
from django.core.exceptions import ValidationError
from django.db import models
from uuidfield import UUIDField

from quark.qldap import utils as ldap_utils


class APIKey(models.Model):
    """A unique key for each user, which can be used for validating special
    access.

    For instance, an API key can be passed as a URL parameter with the user's
    username to validate what the given user has access to.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                related_name='api_key')
    key = UUIDField(auto=True, db_index=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta(object):
        verbose_name = 'API key'

    def __unicode__(self):
        return u'{}: {}'.format(unicode(self.user), self.key)


def create_api_key(sender, instance, created, **kwargs):
    """A receiver for a signal to automatically create an APIKey for users."""
    if created:
        APIKey.objects.create(user=instance)


models.signals.post_save.connect(create_api_key, sender=get_user_model())


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
        norm_email = self.normalize_email(email)
        user = self.model(
            username=username,
            email=norm_email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            **extra_fields)
        user.save()
        return user

    def create_superuser(self, username, email, password,
                         first_name, last_name, **extra_fields):
        return self.create_user(username, email, password,
                                first_name, last_name,
                                is_superuser=True, **extra_fields)


class LDAPUser(get_user_model()):
    """Overrides user model's password facilities.

    User passwords are stored only in LDAP and not in Django, so LDAP is used
    to set and check passwords. Django user objects will be set with unusable
    passwords.

    The LDAPUser cannot be set as the AUTH_USER_MODEL, as it is a proxy model
    for the AUTH_USER_MODEL.
    """

    objects = LDAPUserManager()

    class Meta(object):
        proxy = True
        verbose_name = 'LDAP User'

    def save(self, *args, **kwargs):
        """Only save the instance if user exists in LDAP. Allows renaming
        username, but does not update other LDAP entry attributes (yet)."""
        new_username = self.get_username()
        # Password can be None or '' for unusuable password
        if (not new_username or not self.email or
                not self.first_name or not self.last_name):
            raise ValidationError('Users must have username, email, '
                                  'first name and last name')

        try:
            old_user = LDAPUser.objects.get(pk=self.pk)
            old_username = old_user.get_username()
            renaming_user = old_username != new_username
            updating_email = old_user.email != self.email
        except LDAPUser.DoesNotExist:
            renaming_user = False
            updating_email = False

        # Update username
        if renaming_user:
            success, reason = ldap_utils.rename_user(
                old_username,
                new_username)
            if not success:
                raise ValidationError(
                    'Encountered error while renaming username from {old} '
                    'to {new}. Reason: {reason}'.format(
                        old=old_username,
                        new=new_username,
                        reason=reason))
        elif not ldap_utils.username_exists(new_username):
            if ldap_utils.create_user(new_username, self.password, self.email,
                                      self.first_name, self.last_name):
                # Successfully created LDAP entry for new user
                # Set an unusable password for the Django DB instance
                super(LDAPUser, self).set_unusable_password()
            else:
                # Failed to create user some how.
                raise ValidationError(
                    'Error creating new LDAP entry for {name} with username '
                    '"{username}"'.format(
                        name=self.get_full_name(),
                        username=new_username))

        # Update email
        # New username should exist by now after rename.
        if (updating_email and
                not ldap_utils.set_email(new_username, self.email)):
            raise ValidationError(
                'Encountered error while updating user email to {new}'.format(
                    new=self.email))
        # TODO(flieee): update LDAP other entry attributes (i.e. name) too?
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
        super(LDAPUser, self).set_unusable_password()
        ldap_utils.set_password(self.get_username(), None)


def make_ldap_user(user):
    """Sets the user model for the given user to be the LDAPUser proxy model.
    """
    # Change the user class to the proxy model LDAPUser
    user.__class__ = LDAPUser
