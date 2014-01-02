# pylint: disable=F0401
import quark_keys


DEBUG = False
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('TBP IT', 'it-notice@tbp.berkeley.edu'),
)
MANAGERS = ADMINS

# Only use LDAP in production
USE_LDAP = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'quark_prod',
        'USER': 'quark',
        'PASSWORD': quark_keys.PROD_DB_PASSWORD,
    }
}

# This only goes here because there's no HTTPS support in dev
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
