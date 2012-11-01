# Django settings for quark project - TBP and PiE's merged project.

import getpass
import os
import socket
import sys

KEY_PATH = "/home/tbp/private"
if KEY_PATH not in sys.path:
    sys.path.append(KEY_PATH)
import quark_keys


# Determine the path of your local workspace.
WORKSPACE_DJANGO_ROOT = os.path.abspath(
    os.path.dirname(globals()['__file__']))
WORKSPACE_ROOT = os.path.dirname(WORKSPACE_DJANGO_ROOT)

HOSTNAME = 'tbp.berkeley.edu'

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = ()

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        # We need this for per-user development databases.
        'NAME': 'quark_%s' % getpass.getuser(),
        'USER': 'quark_dev',
        'PASSWORD': quark_keys.DEV_DB_PASSWORD,
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/Los_Angeles'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
# TODO(wli): figure out MEDIA_ROOT
MEDIA_ROOT = ''

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
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = quark_keys.SECRET_KEY

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'quark.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'quark.wsgi.application'

TEMPLATE_DIRS = (
  os.path.join(WORKSPACE_DJANGO_ROOT, 'templates'),
)

# All projects that we write (and thus, need to be tested) should go here.
PROJECT_APPS = [
]

# Third-party apps belong here, since we won't use them for testing.
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.flatpages',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'django_jenkins',
] + PROJECT_APPS

DEFAULT_FROM_EMAIL = 'webmaster@' + HOSTNAME

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

# YouTube Secret Stuff
YT_USERNAME = 'BerkeleyTBP'
YT_PRODUCT = 'noiro'
YT_DEVELOPER_KEY = quark_keys.YT_DEVELOPER_KEY
YT_PASSWORD = quark_keys.YT_PASSWORD

# http://www.djangosnippets.org/snippets/1653/
RECAPTCHA_PRIVATE_KEY = quark_keys.RECAPTCHA_PRIVATE_KEY
RECAPTCHA_PUBLIC_KEY = quark_keys.RECAPTCHA_PUBLIC_KEY

# LDAP password.
LDAP_BASEDN_PW = quark_keys.LDAP_BASEDN_PW

JENKINS_TASKS = (
    'django_jenkins.tasks.django_tests',
    'django_jenkins.tasks.run_csslint',
    'django_jenkins.tasks.run_jslint',
    'django_jenkins.tasks.run_pep8',
    'django_jenkins.tasks.run_pylint',
    'django_jenkins.tasks.with_coverage',
)

###############################################################################
# Import any local settings to override default settings.
###############################################################################
try:
    from settings_local import *
except ImportError:
    # If the file doesn't exist, print a warning message but do not fail.
    print "WARNING: No settings_local file was detected."
###############################################################################
# End local settings section.
###############################################################################

# separate cookies for dev server, dev-tbp, and production
SESSION_COOKIE_NAME = '%s_sessionid' % socket.gethostname().split('.')[0]
if DEBUG:
    SESSION_COOKIE_NAME = 'dbg_' + SESSION_COOKIE_NAME
