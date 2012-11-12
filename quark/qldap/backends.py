from quark.auth.models import User
from quark.qldap import utils
from quark.settings import LDAP


class LDAPBackend:
    supports_object_permissions = False
    supports_anonymous_user = False
    supports_inactive_user = False

    def authenticate(self, username=None, password=None):
        if username is None or password is None:
            return None

        if not utils.check_password(username, password):
            return None

        try:
            user = User.objects.get(username__iexact=username)
        except User.DoesNotExist:
            filter_pattern = '(&(objectClass=inetOrgPerson)(uid=%s))' % (
                username)
            keys = ['uid', 'givenName', 'sn', 'mail']

            ldap_handle = utils.initialize()
            if ldap_handle is None:
                return None
            result = ldap_handle.search_s(
                LDAP['BASE'], LDAP['SCOPE'], filter_pattern, keys)
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

            user = User.objects.create_user(uid, mail)
            user.first_name = user_gn
            user.last_name = user_sn
            user.is_staff = False
            user.save()
        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
