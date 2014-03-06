import base64
import copy
import grp
import hashlib
import hmac
import ldap
import os
import random
import re
import string

from django.conf import settings
from django.contrib.auth.hashers import UNUSABLE_PASSWORD_PREFIX
from django.contrib.auth.hashers import UNUSABLE_PASSWORD_SUFFIX_LENGTH
from django.core.mail import mail_admins
from django.utils.crypto import get_random_string
from django.utils.encoding import smart_bytes


# Compile username validator, or match all if not set.
USERNAME_REGEX = re.compile(settings.VALID_USERNAME or '')

# Use salted SHA1 LDAP passwords
LDAP_HASH_PREFIX = '{SSHA}'
# OpenLDAP salt must be 4 bytes
LDAP_SALT_LENGTH = 4


# smart_bytes is used to convert unicode to byte strings for python-ldap.
# In the future, when python-ldap supports python3/unicode,
# this will no longer be necessary.
def initialize(base_dn=settings.LDAP_BASE['DN'],
               base_pw=settings.LDAP_BASE['PASSWORD']):
    """
    Connects to LDAP and returns a handle for the connection
    If it failed to connect, returns None
    """
    try:
        ldap_handle = ldap.initialize(settings.LDAP['HOST'])
        ldap_handle.protocol_version = ldap.VERSION3
        ldap_handle.simple_bind_s(base_dn, base_pw)
        return ldap_handle
    except ldap.INVALID_CREDENTIALS as e:
        return None
    except ldap.LDAPError as e:
        mail_admins('LDAP Anomaly Detected',
                    'LDAP problem occurred on initialization: %s' % e)
        return None


def username_exists(username):
    """
    Checks if the username is in the People tree.
    Returns True/False, or None upon error.
    """
    ldap_handle = initialize()
    if ldap_handle is None:
        return None

    searchstr = '(uid=%s)' % smart_bytes(username)
    try:
        entry = ldap_handle.search_s(settings.LDAP_BASE['PEOPLE'],
                                     settings.LDAP['SCOPE'],
                                     searchstr)
        return bool(entry)
    except ldap.LDAPError:
        return None


def create_user(username, password, email, first_name, last_name):
    """
    Creates a new user in the People LDAP tree.
    Returns True on success, False otherwise (including errors)
    """
    # All fields except password are required. Fails if any are empty.
    # password is allowed to be '' or None for unusable passwords
    if not (username and email and first_name and last_name):
        return False

    # Username must pass regex
    if USERNAME_REGEX.match(username) is None:
        return False

    ldap_handle = initialize()
    if ldap_handle is None:
        return False

    user_uid = smart_bytes(username)
    user_gn = smart_bytes(first_name)
    user_sn = smart_bytes(last_name)
    mail = smart_bytes(email)

    user_dn = 'uid=%s,%s' % (user_uid, settings.LDAP_BASE['PEOPLE'])
    attr = [
        ('objectClass', ['top', 'inetOrgPerson']),
        ('uid', user_uid),
        ('userPassword', obfuscate(password)),
        ('givenName', user_gn),
        ('sn', user_sn),
        ('cn', '%s %s' % (user_gn, user_sn)),
        ('mail', mail)
    ]

    try:
        ldap_handle.add_s(user_dn, attr)
    except ldap.ALREADY_EXISTS:
        return False

    ldap_handle.unbind()
    return True


def delete_user(username):
    """
    Deletes a user given its username. The username must not be empty.
    Returns True on success, False otherwise (including errors)
    """
    if not username:
        return False

    ldap_handle = initialize()
    if ldap_handle is None:
        return False

    user_uid = smart_bytes(username)
    user_dn = 'uid=%s,%s' % (user_uid, settings.LDAP_BASE['PEOPLE'])

    try:
        ldap_handle.delete_s(user_dn)
    except ldap.LDAPError:
        return False

    ldap_handle.unbind()
    return True


def rename_user(username, new_username):
    """
    Renames a user. Only updates LDAP. Does not save model.
    Both arguments are mandatory.
    Returns a (bool, string) tuple for success and reason.
    """
    if not (username and new_username):
        return (False, 'Invalid username argument(s)')

    ldap_handle = initialize()
    if ldap_handle is None:
        return (False, 'LDAP connection failed')

    username = smart_bytes(username)
    new_username = smart_bytes(new_username)

    # Validate new username
    if USERNAME_REGEX.match(new_username) is None:
        return (False, 'Invalid username. ' + settings.USERNAME_HELPTEXT)

    # Make sure new username not yet taken
    if username_exists(new_username):
        return (False, 'Requested username is already taken')

    old_dn = 'uid=%s,%s' % (username, settings.LDAP_BASE['PEOPLE'])
    new_rdn = 'uid=%s' % (new_username)

    try:
        ldap_handle.rename_s(old_dn, new_rdn)
    except ldap.LDAPError:
        return (False, 'LDAP error while renaming user')

    # Search in posixGroups (i.e. cn=web) for old username and replace
    # with new username. groupOfNames are automatically changed by rename_s
    search_str = '(memberUid=%s)' % (username)
    try:
        group_results = ldap_handle.search_s(
            settings.LDAP_BASE['GROUP'], settings.LDAP['SCOPE'], search_str)
    except ldap.LDAPError:
        return (False, 'LDAP error while searching for group memberships')

    for (gdn, gattr) in group_results:
        new_g = copy.copy(gattr)
        new_g['memberUid'] = [member if member != username else new_username
                              for member in gattr['memberUid']]
        mod_g = ldap.modlist.modifyModlist(gattr, new_g)
        try:
            ldap_handle.modify_s(gdn, mod_g)
        except ldap.LDAPError:
            return (False, 'LDAP error while migrating groups')

    return (True, 'User %s renamed to %s' % (username, new_username))


def mod_user_group(username, group, action=ldap.MOD_ADD):
    """
    Adds or removes a user to/from an LDAP group. Default action is to add.
    Returns True on success, False otherwise (including errors)
    """
    if action not in [ldap.MOD_ADD, ldap.MOD_DELETE]:
        return False

    ldap_handle = initialize()
    if ldap_handle is None:
        return False

    username = smart_bytes(username)
    group = smart_bytes(group)

    gdn = 'cn=%s,%s' % (group, settings.LDAP_BASE['GROUP'])
    if get_group_member_attr(group) == 'memberUid':
        attr = [(action, 'memberUid', username)]
    else:
        udn = 'uid=%s,%s' % (username, settings.LDAP_BASE['PEOPLE'])
        attr = [(action, 'member', udn)]

    try:
        ldap_handle.modify_s(gdn, attr)
    except ldap.LDAPError:
        return False
    return True


def set_password(username, password):
    """
    Sets the user's password, overwriting the old one.
    Returns True on success, False otherwise (including errors)
    """
    ldap_handle = initialize()
    if ldap_handle is None:
        return False

    username = smart_bytes(username)
    udn = 'uid=%s,%s' % (username, settings.LDAP_BASE['PEOPLE'])
    attr = [(ldap.MOD_REPLACE, 'userPassword', obfuscate(password))]

    try:
        ldap_handle.modify_s(udn, attr)
    except ldap.LDAPError:
        return False
    return True


def set_email(username, email):
    """
    Set the email attribute in LDAP. Used for Officer email forwarding.
    Although LDAP allows multiple email attributes, we only allow one.
    """
    ldap_handle = initialize()
    if ldap_handle is None:
        return False

    username = smart_bytes(username)
    email = smart_bytes(email)

    udn = 'uid=%s,%s' % (username, settings.LDAP_BASE['PEOPLE'])
    try:
        email_results = ldap_handle.search_s(
            udn, settings.LDAP['SCOPE'], '(mail=*)')
    except ldap.LDAPError:
        return False

    if len(email_results) == 0:
        attr = [(ldap.MOD_ADD, 'mail', email)]
    else:
        attr = [(ldap.MOD_REPLACE, 'mail', email)]

    try:
        ldap_handle.modify_s(udn, attr)
    except ldap.LDAPError:
        return False
    return True


def get_email(username):
    """
    Gets the user's email attribute from LDAP
    Returns the string (currently bytestring) or False if an error occurred.
    """
    ldap_handle = initialize()
    if ldap_handle is None:
        return False

    username = smart_bytes(username)
    udn = 'uid=%s,%s' % (username, settings.LDAP_BASE['PEOPLE'])
    try:
        entry = ldap_handle.search_s(
            udn, settings.LDAP['SCOPE'], '(mail=*)', ['mail'])
    except ldap.LDAPError:
        return False
    entry_len = len(entry)
    if entry_len == 0:
        mail_admins('LDAP Anomaly Detected',
                    'No search results found for %s in "get_email"' % username)
    elif entry_len > 1:
        entries = []
        for e in entry:
            entries.append(e[0])
        mail_admins('LDAP Anomaly Detected',
                    'Multiple search results for %s in "get_email":\n%s' % (
                        username, '\n'.join(entries)))
        return False
    # Invalid search result. Each search result must be a 2-tuple
    if len(entry[0]) != 2:
        return False
    return get_property(entry[0][1], 'mail') or False


def check_password(username, password):
    """
    Returns True if (unhashed) password matches the user's password in LDAP.
    This authenticates using LDAP bind. Upon a successful bind, it will
    upgrade an MD5 hash to salted SHA1 (SSHA) if applicable.
    """
    ldap_handle = initialize()
    if ldap_handle is None:
        return False

    # don't allow blank username or password
    # This is important because a binding with a blank password can be
    # interpreted as an anonymous bind, which would succeed when it should not.
    if username and password:
        username = smart_bytes(username)
        password = smart_bytes(password)

        # attempt to bind as user
        user_dn = 'uid=%s,%s' % (username, settings.LDAP_BASE['PEOPLE'])
        out = initialize(user_dn, password)
        if out is None:
            return False
        else:
            # Authentication successful; attempt to migrate password
            # Then return success
            searchstr = '(&(objectClass=inetOrgPerson)(uid=%s))' % username
            try:
                pw_result = ldap_handle.search_s(
                    settings.LDAP_BASE['PEOPLE'],
                    settings.LDAP['SCOPE'],
                    searchstr,
                    ['userPassword'])
            except ldap.LDAPError:
                return False
            # pw_result must be of the form:
            # [(DN, {'userPassword': ['password',],}),]
            if len(pw_result) != 1 or len(pw_result[0]) != 2:
                mail_admins('LDAP Anomaly Detected',
                            ('Non-standard password results for %s in'
                             'check_password') % username)
            # Automatically update password to new hash algorithm
            if LDAP_HASH_PREFIX not in pw_result[0][1]['userPassword'][0]:
                set_password(username, password)
            return True
    else:
        # Bad username or password
        return False


def has_usable_password(username):
    """
    Gets the user's password entry from LDAP.
    Returns False if it's an unusable password, or encounters LDAP errors
    """
    ldap_handle = initialize()
    if ldap_handle is None:
        return False

    username = smart_bytes(username)
    try:
        entry = ldap_handle.search_s(
            settings.LDAP_BASE['PEOPLE'],
            settings.LDAP['SCOPE'],
            '(uid=%s)' % username,
            ['userPassword'])
    except ldap.LDAPError:
        return False
    entry_len = len(entry)
    if entry_len != 1:
        mail_admins('LDAP Anomaly Detected',
                    'Found %d userPassword attributes for %s ' % (
                        entry_len,
                        username))
    # Invalid search result. Each search result must be a 2-tuple
    if len(entry[0]) != 2:
        return False
    pw_hash = get_property(entry[0][1], 'userPassword')
    return pw_hash and UNUSABLE_PASSWORD_PREFIX not in pw_hash


def get_property(attributes, key, index=0):
    """
    Get a property from an LDAP search result.
    LDAP result given in attribute, the attribute name to grab given by key,
    and get the index-th result if there are multiple entries of the attribute.
    Returns None if attribute or index not found.
    """
    if attributes.get(key) and len(attributes[key]) > index:
        return attributes[key][index]
    return None


def encode(secret, data):
    """
    Encodes a string in base64 similar to how OpenLDAP stores passwords
    """
    return hmac.new(secret.encode('utf-8'), base64.b64decode(data)).hexdigest()


def obfuscate(password):
    """
    Hashes a password using (salted) SHA1 algorithm.
    Also converts password to byte string before processing.
    A None or '' password is considered unusable.
    Unusable passwords will be corrupted with a UNUSABLE_PASSWORD_PREFIX and
    instead hash a random password.
    OpenLDAP 2.4.x only supports SHA1. Would be nice if they supported
    an algorithm that is more secure.
    """
    hash_prefix = LDAP_HASH_PREFIX
    # Set unusable password if None or empty string
    if not password:
        hash_prefix += UNUSABLE_PASSWORD_PREFIX
        password = get_random_string(
            length=UNUSABLE_PASSWORD_SUFFIX_LENGTH,
            allowed_chars=string.printable)
    try:
        salt = os.urandom(LDAP_SALT_LENGTH)
    except NotImplementedError:
        salt = ''.join(
            [chr(random.randint(0, 255)) for _ in range(LDAP_SALT_LENGTH)])
    hmsg = hashlib.new('sha1')
    # openldap SSHA uses this format:
    # '{SSHA}' + b64encode(sha1_digest('secret' + 'salt') + 'salt')
    hmsg.update(smart_bytes(password))
    hmsg.update(salt)
    pw_hash = base64.b64encode(hmsg.digest() + salt)
    return smart_bytes(hash_prefix + pw_hash)


def is_group_member(username, group):
    """
    Checks if the user is a member of an LDAP Group.
    Returns False if any errors are encountered
    """
    ldap_handle = initialize()
    if ldap_handle is None:
        return False

    username = smart_bytes(username)
    group = smart_bytes(group)

    filter_pattern = '(&(cn=%s)(|(memberUid=%s)(member=uid=%s,%s)))' % (
        group, username, username, settings.LDAP_BASE['PEOPLE'])

    try:
        result = ldap_handle.search_s(settings.LDAP_BASE['GROUP'],
                                      settings.LDAP['SCOPE'],
                                      filter_pattern)
    except ldap.LDAPError:
        return False

    return len(result) > 0


def create_group(group, object_class='groupOfNames'):
    """
    Create a new ldap group, either of class groupOfNames or posixGroup.
    The group is initialized with the default user if it is a groupOfNames,
    and initialized with no users if it is posixGroup.
    The parameter 'group' specifies the new group name.
    Note that typically, group names for TBP-specific groups begin with "tbp-",
    to differentiate from similarly named groups in other organizations that
    may share the same LDAP directory.
    """
    if object_class not in ['groupOfNames', 'posixGroup']:
        return False

    ldap_handle = initialize()
    if ldap_handle is None:
        return False

    group_dn = 'cn=%s,%s' % (group, settings.LDAP_BASE['GROUP'])
    attr = [
        ('objectClass', ['top', object_class]),
        ('cn', group),
    ]

    if object_class == 'groupOfNames':
        # groupOfNames objectClass requires at least one member in the group
        # at all times, so add the default user to this new groupOfNames group
        # initially. (Note that the default user can later be removed after
        # other members have been added, if desired.)
        attr.append(('member', settings.LDAP_DEFAULT_USER))
    else:
        attr.append(('gidNumber', str(generate_new_gidnumber())))

    try:
        ldap_handle.add_s(group_dn, attr)
    except ldap.LDAPError:
        return False

    ldap_handle.unbind()
    return True


def generate_new_gidnumber():
    """
    Returns a gidNumber that is not currently in use by another group and is in
    the range [2001, 65533]. The function finds the current highest value gid
    in that range and adds 1 to it to create a new gid.
    """
    ldap_handle = initialize()
    if ldap_handle is None:
        return False

    # Search for any group:
    searchstr = '(cn=*)'
    try:
        entries = ldap_handle.search_s(settings.LDAP_BASE['GROUP'],
                                       settings.LDAP['SCOPE'],
                                       searchstr)
    except ldap.LDAPError:
        return False

    min_gid = 2001
    max_gid = 65533
    current_gids = []

    # Find all current gidNumbers used by LDAP groups:
    for entry in entries:
        entry_properties = entry[1]
        if 'gidNumber' in entry_properties:
            # Note that entry_properties['gidNumber'] returns a list, but each
            # entry can only have one gidNumber, so the list will be of length
            # 1 and the gidNumber will be at index 0. Also note that the
            # gidNumber will appear as a string instead of an int in that list,
            # so it must be converted to an int:
            current_gids.append(int(entry_properties['gidNumber'][0]))

    # Find all current gidNumbers used by unix groups:
    for group_struct in grp.getgrall():
        # gid is stored as a number at the second index in the group structures
        # returned by grp.getgrall()
        current_gids.append(group_struct[2])

    relevant_gids = [gid for gid in current_gids
                     if min_gid <= gid <= max_gid]

    if relevant_gids:
        # if relevant_gids is non-empty (that is, there were gids currently in
        # use within the [min_gid, max_gid] range)
        return max(relevant_gids) + 1
    else:
        return min_gid


def delete_group(group):
    """
    Deletes an LDAP group
    Returns False if any errors were encountered
    """
    ldap_handle = initialize()
    if ldap_handle is None:
        return False

    group = smart_bytes(group)
    group_dn = 'cn=%s,%s' % (group, settings.LDAP_BASE['GROUP'])

    try:
        ldap_handle.delete_s(group_dn)
    except ldap.LDAPError:
        return False

    ldap_handle.unbind()
    return True


def group_exists(group):
    """
    Checks if the group is in the Group LDAP tree
    Returns True/False, or None upon error.
    """
    ldap_handle = initialize()
    if ldap_handle is None:
        return None

    group = smart_bytes(group)
    searchstr = '(cn=%s)' % group
    try:
        entry = ldap_handle.search_s(settings.LDAP_BASE['GROUP'],
                                     settings.LDAP['SCOPE'],
                                     searchstr)
        return bool(entry)
    except ldap.LDAPError:
        return None


def get_group_member_attr(group):
    """
    Returns the group member attribute type for this group: "member" if this
    group is of the objectClass groupOfNames, or "memberUid" if it is of the
    objectClass posixGroup.
    """
    ldap_handle = initialize()
    if ldap_handle is None:
        return False

    group = smart_bytes(group)
    searchstr = '(cn=%s)' % group
    try:
        entry = ldap_handle.search_s(settings.LDAP_BASE['GROUP'],
                                     settings.LDAP['SCOPE'],
                                     searchstr)
    except ldap.LDAPError:
        return False

    # Should only return one successful entry (since there should only be one
    # group that matches the group parameter used with this function)
    if len(entry) != 1 or len(entry[0]) != 2:
        return False

    entry_properties = entry[0][1]
    group_classes = entry_properties['objectClass']
    if 'posixGroup' in group_classes:
        member_attribute = 'memberUid'
    elif 'groupOfNames' in group_classes:
        member_attribute = 'member'
    else:
        return False
    return member_attribute


def get_group_members(group):
    """
    Return a list of the members in the group.
    """
    ldap_handle = initialize()
    if ldap_handle is None:
        return False

    group = smart_bytes(group)
    searchstr = '(cn=%s)' % group
    try:
        entry = ldap_handle.search_s(settings.LDAP_BASE['GROUP'],
                                     settings.LDAP['SCOPE'],
                                     searchstr)
    except ldap.LDAPError:
        return False

    # Should only return one successful entry (since there should only be one
    # group that matches the group parameter used with this function)
    if len(entry) != 1 or len(entry[0]) != 2:
        return False

    member_attribute = get_group_member_attr(group)
    entry_properties = entry[0][1]
    if member_attribute in entry_properties:
        return entry_properties[member_attribute]
    else:
        # It is possible for a posixGroup to have no members, in which case
        # 'memberUid' will not be listed in the entry's properties, indicating
        # that there are no members (so return an empty list):
        return []


def clear_group_members(group):
    """
    Clears all members from an ldap group. If the group requires at least one
    member, then the function ensures that the default user remains in the
    group. Returns True upon successful completion, False otherwise.
    """
    ldap_handle = initialize()
    if ldap_handle is None:
        return False

    group = smart_bytes(group)
    searchstr = '(cn=%s)' % group
    try:
        entry = ldap_handle.search_s(settings.LDAP_BASE['GROUP'],
                                     settings.LDAP['SCOPE'],
                                     searchstr)
    except ldap.LDAPError:
        return False

    # Should only return one successful entry (since there should only be one
    # group that matches the group parameter used with this function)
    if len(entry) != 1 or len(entry[0]) != 2:
        return False

    group_dn = entry[0][0]
    entry_properties = entry[0][1]
    group_classes = entry_properties['objectClass']
    members = get_group_members(group)
    member_attribute = get_group_member_attr(group)

    if settings.LDAP_DEFAULT_USER in members:
        # Do not wish to remove the default user from the ldap group, so remove
        # it from the members list
        members.remove(settings.LDAP_DEFAULT_USER)
    elif 'groupOfNames' in group_classes:
        # If the default user is not in the list of members and the group is in
        # the groupOfNames class (implying that the group requires at least 1
        # member in the group), then add the default user to the ldap group,
        # but not to the list "members" (to prevent the default user from being
        # subsequently removed)
        modlist = [(ldap.MOD_ADD, member_attribute, settings.LDAP_DEFAULT_USER)]
        ldap_handle.modify_s(group_dn, modlist)

    modlist = [(ldap.MOD_DELETE, member_attribute, member)
               for member in members]

    try:
        ldap_handle.modify_s(group_dn, modlist)
    except ldap.LDAPError:
        return False
    return True


# TODO(flieee): move else where or delete for quark tbp/pie repo split
def is_tbp(username):
    """
    Convenience method for checking if a username is in any of TBP groups.
    """
    return is_group_member(username, 'tbp-*')


def is_in_tbp_group(username, group):
    """
    Convenience method for checking if a username is part of a specified TBP
    LDAP group, entered as a string (e.g., 'members' or 'officers').
    """
    return is_group_member(username, 'tbp-%s' % group)


def is_pie(username):
    """
    Convenience method for checking if a username is in any of the PIE groups.
    """
    return is_group_member(username, 'pie-*')


def is_pie_staff(username):
    """
    Convenience method for checking if a username is in the staff pie group.
    """
    return is_group_member(username, 'pie-staff')
