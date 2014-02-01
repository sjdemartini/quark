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
