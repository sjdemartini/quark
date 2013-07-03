# pylint: disable=F0401
import quark_keys


DEBUG = False
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('TBP IT', 'it-notice@tbp.berkeley.edu'),
    ('PiE IT', 'it-notice@pioneers.berkeley.edu'))
MANAGERS = ADMINS

# Only use LDAP user in production. Just use QuarkUser for staging.
# If you believe LDAP causes issues in production, change it locally to test
AUTH_USER_MODEL = 'accounts.QuarkUser'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'quark_dev_staging',
        'USER': 'quark_dev',
        'PASSWORD': quark_keys.DEV_DB_PASSWORD,
    }
}

# This only goes here because there's no HTTPS support in dev
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
