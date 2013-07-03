"""
Default settings for running jenkins
"""

# pylint: disable=W0401,W0614
from quark.settings import *

DEBUG = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'quark_test.db',
    },
}

# Use nonLDAP model
AUTH_USER_MODEL = 'accounts.QuarkUser'

# We don't need to test these apps.
BLACKLISTED_APPS = ['django_evolution', 'django.contrib.flatpages', 'south']
for app in BLACKLISTED_APPS:
    if app in INSTALLED_APPS:
        INSTALLED_APPS.remove(app)

# These middleware classes mess up testing.
BLACKLISTED_MIDDLEWARE = [
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware']
for middleware in BLACKLISTED_MIDDLEWARE:
    if middleware in MIDDLEWARE_CLASSES:
        MIDDLEWARE_CLASSES.remove(middleware)
