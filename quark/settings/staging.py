# pylint: disable=F0401
import quark_keys


DEBUG = False
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('TBP IT', 'it-notice@tbp.berkeley.edu'),
)
MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'quark_dev_staging',
        'USER': 'quark_dev',
        'PASSWORD': quark_keys.DEV_DB_PASSWORD,
    }
}

# Only use LDAP in production/staging
USE_LDAP = True

# HTTPS support in staging
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

# Import any local settings custom for staging environment
try:
    # pylint: disable=F0401,W0401,W0614
    from quark.settings.local import *
except ImportError:
    # Ignore if there's no local settings file
    pass
