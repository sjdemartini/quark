from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

from quark.qldap import utils


# pylint: disable=C0103
User = get_user_model()


class LDAPBackend(ModelBackend):
    """An authentication backend which checks user name and password in the
    LDAP database.

    The backend creates a new Django user if the user is found in the LDAP
    database (with matching password) but does not exist in the Django
    database.

    Note that this backend is only active if the settings attribute USE_LDAP
    is set to True; otherwise it does nothing.
    """
    supports_object_permissions = False
    supports_anonymous_user = False
    supports_inactive_user = False

    def authenticate(self, username=None, password=None):
        if not getattr(settings, 'USE_LDAP', False):
            # Must have USE_LDAP set to True to authenticate with this backend
            return None

        if username is None or password is None:
            return None

        if not utils.check_password(username, password):
            return None

        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return self.__create_user(username)

    def get_user(self, user_id):
        if not getattr(settings, 'USE_LDAP', False):
            # Must have USE_LDAP set to True to authenticate with this backend
            return None

        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    def __create_user(self, username):
        """
        Helper function for creating Django users out of existing LDAP users
        Migrates username, first and last name, and email
        If this is a dev session (DEBUG == True), also make tbp/pie-it members
        superusers.
        """
        filter_pattern = '(&(objectClass=inetOrgPerson)(uid=%s))' % username
        keys = ['uid', 'givenName', 'sn', 'mail']

        ldap_handle = utils.initialize()
        if ldap_handle is None:
            return None
        result = ldap_handle.search_s(
            settings.LDAP['BASE'],
            settings.LDAP['SCOPE'],
            filter_pattern, keys)
        # Result list should have exactly one element,
        # which is a 2-tuple of DN and dictionary of attributes
        if len(result) != 1 or len(result[0]) != 2:
            return None

        attr = result[0][1]
        uid = utils.get_property(attr, 'uid')
        if uid is None:
            return None

        user_gn = utils.get_property(attr, 'givenName')
        user_sn = utils.get_property(attr, 'sn')
        mail = utils.get_property(attr, 'mail') or ''

        # Use direct model instantiation to skip LDAP entry creation
        migrate_user = User(
            username=uid,
            email=mail,
            first_name=user_gn,
            last_name=user_sn)
        migrate_user.set_unusable_password()

        # Set superuser if user is in tbp-it or pie-it, but only if this is
        # a dev server via settings.DEBUG = True
        if settings.DEBUG and utils.is_group_member(uid, '*-it'):
            migrate_user.is_superuser = True
            migrate_user.is_staff = True
        migrate_user.save()

        # Return saved version of user
        # TODO(flieee): move to a shortcut module func for general use
        try:
            return User.objects.get(username=uid)
        except User.DoesNotExist:
            return None
