# pylint: disable=F0401
import quark_keys
from quark.settings.project import HOSTNAME
from quark.settings.project import RESUMEQ_OFFICER_POSITION


DEBUG = False
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('TBP IT', 'it-notice@' + HOSTNAME),
)
MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'quark_prod',
        'USER': 'quark',
        'PASSWORD': quark_keys.PROD_DB_PASSWORD,
    }
}

# Only use LDAP in production/staging
USE_LDAP = True

# HTTPS support in production
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

# Email addresses
RESUMEQ_ADDRESS = RESUMEQ_OFFICER_POSITION + '@' + HOSTNAME
HELPDESK_ADDRESS = 'helpdesk@' + HOSTNAME
INDREL_ADDRESS = 'indrel@' + HOSTNAME
IT_ADDRESS = 'it@' + HOSTNAME
STARS_ADDRESS = 'stars@' + HOSTNAME

HELPDESK_NOTICE_TO = 'notice@' + HOSTNAME
INDREL_NOTICE_TO = 'notice@' + HOSTNAME
HELPDESK_SPAM_TO = 'spam@' + HOSTNAME
INDREL_SPAM_TO = 'spam@' + HOSTNAME
