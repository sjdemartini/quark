"""
Django settings for "quark" student organization website project.

This file lists Django settings constant for development and production
environments. Never import this directly unless you are sure you do not need
the settings in the site- or env-specific settings files.
"""

import os
import sys
import warnings

KEY_PATH = '/home/tbp/private'
if KEY_PATH not in sys.path:
    sys.path.append(KEY_PATH)
try:
    # pylint: disable=F0401
    import quark_keys
except ImportError:
    print('Could not import quark_keys. Please make sure quark_keys.py exists '
          'on the path, and that there are no errors in the module.')
    sys.exit(1)


# Determine the path of your local workspace.
WORKSPACE_DJANGO_ROOT = os.path.abspath(
    os.path.dirname(os.path.dirname(globals()['__file__'])))
WORKSPACE_ROOT = os.path.dirname(WORKSPACE_DJANGO_ROOT)

DEBUG = False
TEMPLATE_DEBUG = DEBUG

ADMINS = ()

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        # You shouldn't be using this database
        'NAME': 'improper_quark.db',
    }
}

# Use 'app_label.model_name'
# Currently use django.contrib.auth.User.
AUTH_USER_MODEL = 'auth.User'

# USE_LDAP indicates when an LDAP proxy model (accounts.LDAPUser) for users
# (proxies AUTH_USER_MODEL) should be used. When USE_LDAP is True, the LDAP
# authentication backend becomes active, and user account forms (like changing
# passwords) use the LDAPUser proxy model.
USE_LDAP = False  # Only use LDAP in production

AUTHENTICATION_BACKENDS = (
    'quark.qldap.backends.LDAPBackend',
    'django.contrib.auth.backends.ModelBackend',
)

LOGIN_REDIRECT_URL = '/'
LOGIN_URL = 'accounts:login'
LOGOUT_URL = 'accounts:logout'
REDIRECT_FIELD_NAME = 'next'

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/Los_Angeles'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en'

LANGUAGES = [
    ('en', 'English'),
]

# ODD for dev (n), EVEN for production (n+1)
# Make sure your dev/production site uses the correct SITE_ID
SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

if USE_TZ:
    # Raise an error when dealing with timezone-unaware objects.
    warnings.filterwarnings(
        'error', r'DateTimeField received a naive datetime',
        RuntimeWarning, r'django\.db\.models\.fields')

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = os.path.join(WORKSPACE_ROOT, 'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(WORKSPACE_ROOT, 'static')

# URL prefix for static files.
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(WORKSPACE_DJANGO_ROOT, 'static'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
    # django-compressor file finder
    'compressor.finders.CompressorFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = quark_keys.SECRET_KEY

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
    #'django.core.context_processors.i18n',
    'django.core.context_processors.request',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
)

MIDDLEWARE_CLASSES = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.doc.XViewMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
]

ROOT_URLCONF = 'quark.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'quark.wsgi.application'

TEMPLATE_DIRS = (
    os.path.join(WORKSPACE_DJANGO_ROOT, 'templates'),
)

DJANGO_CONTRIB_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.flatpages',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.staticfiles',
]

# All projects that we write (and thus, need to be tested) should go here.
PROJECT_APPS = [
    'quark.accounts',
    'quark.achievements',
    'quark.base',
    'quark.candidates',
    'quark.courses',
    'quark.course_surveys',
    'quark.emailer',
    'quark.events',
    'quark.exams',
    'quark.mailing_lists',
    'quark.minutes',
    'quark.newsreel',
    'quark.past_presidents',
    'quark.project_reports',
    'quark.qldap',
    'quark.quote_board',
    'quark.resumes',
    'quark.user_profiles',
    'quark.utils',
    'quark.vote',
]

# Third-party apps belong here, since we won't use them for testing.
THIRD_PARTY_APPS = [
    'chosen',
    'compressor',
    'debug_toolbar',
    'django_jenkins',
    'easy_thumbnails',
    'localflavor',
    'south',  # For data migration
]

# This is the actual variable that django looks at.
INSTALLED_APPS = DJANGO_CONTRIB_APPS + PROJECT_APPS + THIRD_PARTY_APPS

# Mailman path
MMPATH = '/usr/lib/mailman'
if MMPATH not in sys.path:
    sys.path.append(MMPATH)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}


###############################################################################
# Import any extra settings to override default settings.
###############################################################################
try:
    # pylint: disable=W0401,W0614
    from quark.settings.project import *
    from quark.settings.third_party import *
except ImportError as err:
    # If the file doesn't exist, print a warning message but do not fail.
    print('WARNING: %s' % str(err))


###############################################################################
# Import the proper instance environment settings (dev/production/staging)
# Errors will be raised if the appropriate settings file is not found
###############################################################################
__quark_env__ = os.getenv('QUARK_ENV', 'dev')
# pylint: disable=W0401,W0614
if __quark_env__ == 'dev':
    from quark.settings.dev import *
elif __quark_env__ == 'staging':
    from quark.settings.staging import *
elif __quark_env__ == 'production':
    from quark.settings.production import *
else:
    print('WARNING: Invalid value for QUARK_ENV: %s' % __quark_env__)
