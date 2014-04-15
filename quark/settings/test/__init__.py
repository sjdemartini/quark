"""Default settings for running tests."""

# pylint: disable=W0401,W0614
from quark.settings import *

DEBUG = False
USE_LDAP = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'quark_test.db',
    },
}

# Use a dummy cache for the default cache during testing
CACHES['default'] = {
    'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
}

# TODO(sjdemartini): Don't "blacklist" any third party apps and get tests to
# pass (since we ought to be testing under the same circumstances and with the
# same apps as what the full website will have)

# We don't need to test these apps.
BLACKLISTED_APPS = ['django_evolution', 'south', 'debug_toolbar']
for app in BLACKLISTED_APPS:
    if app in INSTALLED_APPS:
        INSTALLED_APPS.remove(app)

# These middleware classes mess up testing.
BLACKLISTED_MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware'
]
for middleware in BLACKLISTED_MIDDLEWARE:
    if middleware in MIDDLEWARE_CLASSES:
        MIDDLEWARE_CLASSES.remove(middleware)
