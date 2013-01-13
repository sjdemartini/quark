"""
Settings introduced by Quark

Note: The values given here are intended for development. A production
environment would overwrite these. The base and site-specific settings files
must not overwrite these.
"""
"""Settings introduced by Quark"""
import ldap
import quark_keys


# TODO(nitishp) Add actual emails (noiro was missing them too...)
# Emailer stuff
ENABLE_HELPDESKQ = False

RESUMEQ_CC_ADDRESS = 'test@tbp.berkeley.edu'

# Email addresses
HELPDESK_ADDRESS = 'test@tbp.berkeley.edu'
INDREL_ADDRESS = 'test@tbp.berkeley.edu'
IT_ADDRESS = 'test@tbp.berkeley.edu'
STARS_ADDRESS = 'test@tbp.berkeley.edu'

# Should we cc people who ask us questions?
HELPDESK_CC_ASKER = False

# Do we send spam notices?
HELPDESK_SEND_SPAM_NOTICE = True
INDREL_SEND_SPAM_NOTICE = True
# where?
HELPDESK_NOTICE_TO = 'test@tbp.berkeley.edu'
INDREL_NOTICE_TO = 'test@tbp.berkeley.edu'

# Do we send messages known to be spam?
HELPDESK_SEND_SPAM = False
INDREL_SEND_SPAM = False
# where?
HELPDESK_SPAM_TO = 'test@tbp.berkeley.edu'
INDREL_SPAM_TO = 'test@tbp.berkeley.edu'

# YouTube Secret Stuff
YT_USERNAME = 'BerkeleyTBP'
YT_PRODUCT = 'noiro'
YT_DEVELOPER_KEY = quark_keys.YT_DEVELOPER_KEY
YT_PASSWORD = quark_keys.YT_PASSWORD

# http://www.djangosnippets.org/snippets/1653/
RECAPTCHA_PRIVATE_KEY = quark_keys.RECAPTCHA_PRIVATE_KEY
RECAPTCHA_PUBLIC_KEY = quark_keys.RECAPTCHA_PUBLIC_KEY

# LDAP settings
LDAP = {
    'HOST': 'ldap://localhost',
    'BASE': 'dc=tbp,dc=berkeley,dc=edu',
    'SCOPE': ldap.SCOPE_SUBTREE,
}
LDAP_BASE = {
    'PEOPLE': 'ou=People,' + LDAP['BASE'],
    'GROUP': 'ou=Group,' + LDAP['BASE'],
    'DN': 'uid=ldapwriter,ou=System,' + LDAP['BASE'],
    'PASSWORD': quark_keys.LDAP_BASEDN_PASSWORD,
}
LDAP_GROUPS = {
    'TBP': ['tbp-officers', 'tbp-members', 'tbp-candidates'],
    'PIE': ['pie-mentors', 'pie-it', 'pie-staff', 'pie-students',
            'pie-teachers'],
}
LDAP_DEFAULT_USER = 'uid=default,ou=System,' + LDAP['BASE']

# LDAP and CustomUser (QuarkUser) valid username regex
# Please use raw string notation (i.e. r'text') to keep regex sane.
# Update quark/qldap/tests.py: test_valid_username_regex() to match
VALID_USERNAME = r'^[a-z][a-z0-9]{2,29}$'
USERNAME_HELPTEXT = ('Username must be 3-30 character, start with a letter,'
                     ' and use only lowercase letters and numbers.')

# Valid types are 'semester' and 'quarter'.
TERM_TYPE = 'semester'
